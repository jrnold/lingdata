#' ---
#' title: Download, process, and insert WALS data into a SQLite database
#' ---
#'
#' Tidies the WALS dataset to make it easier for analyis.
#' Dumps the results to a SQLite database
suppressPackageStartupMessages({
  library("tidyverse")
  library("stringr")
  library("assertthat")
  library("RSQLite")
})

URL <- str_c("https://cdstar.shh.mpg.de/bitstreams/",
             "EAEA0-28CA-1D0B-37B8-0/wals_language.csv.zip")
INPUTS <- list(wals_updates = "data-raw/wals-updates.csv")
OUTFILE <- "wals.db"
VERSION <- "1.0.0"

# 1/2 circumference of the earth
ANTIPODE_DIST <- base::pi * 6378137

# Load WALS data and patch it to fix some issues in the data
wals_updates <- read_csv(INPUTS$wals_updates,
                         na = "",
                         col_types =
                           cols_only(
                             wals_code = col_character(),
                             iso_code = col_character(),
                             macroarea = col_character()
                           ))
walszipfile <- tempfile()
download.file(URL, walszipfile)

wals <-
  read_csv(unz(walszipfile, "language.csv"),
                    col_types = cols(
                      .default = col_character(),
                      latitude = col_double(),
                      longitude = col_double()
                    ), na = "") %>%
   left_join(select(wals_updates,
                    wals_code,
                    `_iso_code` = iso_code,
                    `_macroarea` = macroarea),
             by = "wals_code") %>%
   mutate(iso_code = coalesce(`_iso_code`, iso_code),
          macroarea = coalesce(`_macroarea`, macroarea)) %>%
   select(-matches("^_")) %>%
  ungroup()

#' check that WALS codes are still unique ID
assert_that(!any(duplicated(wals$wals_code)))

#' The database should already have been created and initialized
conn <- dbConnect(RSQLite::SQLite(), OUTFILE)   # nolint

write_table <- function(df, name) {
  # conn from the environment
  dbWriteTable(conn, name, df, overwrite = FALSE, append = TRUE)  # nolint
}

wals %>%
  distinct(macroarea) %>%
  arrange(macroarea) %>%
  write_table("macroareas")

wals %>%
  distinct(genus, family) %>%
  arrange(family, genus) %>%
  write_table("genuses")

wals %>%
  distinct(family) %>%
  arrange(family) %>%
  write_table("families")


#' Language level variables
select(wals, -matches("^\\d+"), -countrycodes) %>%
  write_table("languages")

select(wals, wals_code, countrycodes) %>%
  mutate(countrycodes = str_split(countrycodes, " ")) %>%
  unnest() %>%
  rename(countrycode = countrycodes) %>%
  write_table("language_countries")

wals_features <-
  tibble(variable_ = str_subset(names(wals), "^\\d+")) %>%
  mutate(feature_id = map_chr(str_match_all(variable_, "(\\d+[A-Z])"), 2),
         feature_name = map_chr(str_match_all(variable_, "\\d+[A-Z] (.*)"),
                                2)) %>%
  select(-variable_) %>%
  # substantive area of the features
  # not in data. listed on http://wals.info/feature
  mutate(num = as.integer(str_extract(feature_id, "[0-9]+")),
         area = case_when(
           between(num, 1, 39) ~ "Phonology",
           between(num, 20, 29) ~ "Morphology",
           between(num, 30, 57) ~ "Nominal Categories",
           between(num, 58, 64) ~ "Nominal Syntax",
           between(num, 65, 80) ~ "Verbal Categories",
           between(num, 81, 97) ~ "Word Order",
           between(num, 98, 121) ~ "Simple Clauses",
           between(num, 122, 128) ~ "Complex Sentences",
           between(num, 129, 138) ~ "Lexicon",
           between(num, 139, 140) ~ "Sign Languages",
           between(num, 141, 142) ~ "Other",
           between(num, 143, 144) ~ "Word Order"
         )) %>%
  select(-num) %>%
  # need this to sort them correctly
  arrange(str_pad(feature_id, width = 4, side = "left", "0"))

wals_features %>% write_table("features")

#' Data frame of WALS features with the following columns:
#'
#' - wals_code: WALS language code
#' - feature_number: Feature number, e.g. 1A
#' - feature_name: Feature name or description, e.g. "Consonant Inventories"
#' - value_number: Value number, e.g. 1, 2, 3, ..., 5
#' - value_name: Value name, e.g. "Moderately small", "Large", "Small"
#'
wals %>%
  ungroup() %>%
  select(matches("^\\d+")) %>%
  gather(variable_, value_, na.rm = TRUE) %>%
  distinct() %>%
  mutate(feature_id = map_chr(str_match_all(variable_, "(\\d+[A-Z])"), 2),
         value = as.integer(map_chr(str_match_all(value_, "^(\\d+) "), 2)),
         label = map_chr(str_match_all(value_, "^\\d+ (.*)$"), 2)) %>%
  select(-variable_, -value_) %>%
  arrange(str_pad(feature_id, width = 4, side = "left", "0"), value) %>%
  write_table("feature_values")

wals_language_features <-
  wals %>%
  ungroup() %>%
  select(wals_code, matches("^\\d+")) %>%
  gather(variable_, value_, -wals_code, na.rm = TRUE) %>%
  mutate(feature_id = map_chr(str_match_all(variable_, "(\\d+[A-Z])"), 2),
         value = as.integer(map_chr(str_match_all(value_, "^(\\d+) "), 2))) %>%
  select(-variable_, -value_) %>%
  arrange(wals_code, str_pad(feature_id, width = 4, side = "left", "0"))

write_table(wals_language_features, "language_features")

dist_geo_clade <-
  wals %>%
  select(wals_code, longitude, latitude, family, genus) %>% {
    crossing(., .)
  } %>%
  # remove self-matches
  filter(wals_code < wals_code1) %>%
  mutate(geo = geosphere::distGeo(cbind(longitude, latitude),
                                  cbind(longitude1, latitude1)) /
           ANTIPODE_DIST,
         clade = case_when(
           genus == genus1 ~ 1 / 3,
           family == family1 ~ 2 / 3,
           TRUE ~ 1)
         ) %>%
  select(-matches("latitude|longitude|family|genus")) %>%
  rename(wals_code_1 = wals_code, wals_code_2 = wals_code1) %>%
  gather(variable, value, -wals_code_1, -wals_code_2)

feature_comp <- wals_language_features %>%
  select(wals_code, feature_id, value) %>%
  inner_join(., ., by = "feature_id", suffix = c("_1", "_2")) %>%
  filter(wals_code_1 < wals_code_2) %>%
  mutate(diff = value_1 != value_2) %>%
  select(-value_1, -value_2)

feature_dist <- feature_comp %>%
  group_by(wals_code_1, wals_code_2) %>%
  summarise(value = sum(diff) / length(diff)) %>%
  mutate(variable = "features")

feature_dist_area <- feature_comp %>%
  left_join(select(wals_features, feature_id, area),
            by = "feature_id") %>%
  mutate(variable = str_to_lower(str_replace(area, " +", "_"))) %>%
  group_by(wals_code_1, wals_code_2, variable) %>%
  summarise(value = sum(diff) / length(diff))

bind_rows(dist_geo_clade, feature_dist, feature_dist_area) %>%
  arrange(variable, wals_code_1, wals_code_2) %>%
  write_table("distances")
