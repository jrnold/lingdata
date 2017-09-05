#' ---
#' title: WALS Data
#' ---
#'
#' Tidies the WALS dataset to make it easier for analyis.
#'
#' - `languages`: Data frame data and metadata.
#' - `features`: Data frame of language features in a long format.
#'    Each row is a (language, feature).
#'
library("tidyverse")

# Load WALS data and patch it to fix some issues in the data
wals_updates <- read_csv(project_path("afrobarometer-languages",
                                      "data-raw", "wals-updates.csv"),
                         na = "",
                         col_types =
                           cols_only(
                             wals_code = col_character(),
                             iso_code = col_character(),
                             macroarea = col_character()
                           ))
wals_raw <-
  read_csv(project_path("data-raw", "external", "wals", "language.csv"),
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
assert_that(!any(duplicated(wals_raw$wals_code)))

#' Final data is a list of data frames
wals <- list()

#' Language level variables
wals[["languages"]] <- select(wals_raw, -matches("^\\d+"))

#' Create WALS feature long
#'
#' Data frame of WALS features with the following columns:
#'
#' - wals_code: WALS language code
#' - feature_number: Feature number, e.g. 1A
#' - feature_name: Feature name or description, e.g. "Consonant Inventories"
#' - value_number: Value number, e.g. 1, 2, 3, ..., 5
#' - value_name: Value name, e.g. "Moderately small", "Large", "Small"
#'
wals[["language_features"]] <-
  wals_raw %>%
  ungroup() %>%
  select(wals_code, matches("^\\d+")) %>%
  gather(variable_, value_, -wals_code, na.rm = TRUE) %>%
  mutate(feature_id = map_chr(str_match_all(variable_, "(\\d+[A-Z])"), 2),
         feature_name = map_chr(str_match_all(variable_, "\\d+[A-Z] (.*)"),
                                2),
         value = as.integer(map_chr(str_match_all(value_, "^(\\d+) "), 2)),
         label = map_chr(str_match_all(value_, "^\\d+ (.*)$"), 2)) %>%
  select(-variable_, -value_)

wals[["features"]] <-
  select(wals[["language_features"]], feature_id, feature_name) %>%
  distinct()

wals[["feature_values"]] <-
  select(wals[["language_features"]], feature_id, value, label) %>%


#' Create counts and proportions of features by common groupings
wals[["feature_counts"]] <-
  list(
     genus = left_join(wals$language_features,
                       wals$languages, by = "wals_code") %>%
      count(feature_id, value, genus) %>%
      group_by(feature_id, genus) %>%
      mutate(p = n / sum(n)),
    family = left_join(wals$language_features,
                       wals$languages, by = "wals_code") %>%
      count(feature_id, value, family) %>%
      group_by(feature_id, family) %>%
      mutate(p = n / sum(n)),
    macroarea = left_join(wals$language_features,
                          wals$languages, by = "wals_code") %>%
      count(feature_id, macroarea, value) %>%
      group_by(feature_id, macroarea) %>%
      mutate(p = n / sum(n)),
    total = left_join(wals$language_features,
                      wals$languages, by = "wals_code") %>%
      count(feature_id, value) %>%
      group_by(feature_id) %>%
      mutate(p = n / sum(n))
  )

distances <-
  select(wals_languages, wals_code, longitude, latitude, family, genus) %>%
  crossing(.) %>%
  # remove self-matches
  filter(wals_code < wals_code1) %>%
  mutate(geo = geosphere::distGeo(cbind(longitude, latitude),
                                  cbind(longitude1, latitude1)),
         clade = if_else(genus == genus1, 1, if_else(family == family1, 2, 3)))

