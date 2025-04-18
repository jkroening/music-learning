###############################################################################
## Takes a tab-separated csv of a playlist exported from iTunes/Apple Music of
## the new albums/eps to add, downloads the pertinent info from Spotify, parses
## it, combines the tables, and updated and sorts it. It also requires that up-
## to-date tab-separated csv tables (exported from Wordpress TablePress plugin)
## of the current power rankings have been downloaded and placed in the input
## folder. The finished tables can then be imported back in to TablePress.
##
## This script depends on the playlist exported from iTunes having album ratings
## in the BPM field and "[EP]" or " - EP" in the Album field to distinguish EPs
## from full length albums (LPs). The script will also perform some validations
## to ensure that the music is properly tagged for building the table of
## rankings with complete and clean metadata.
###############################################################################

suppressMessages(library(spotifyR))
suppressMessages(library(dplyr))
suppressMessages(library(stringi))
source("power-routines.R")
options(warn = 1)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) == 0) {
    stop("Must provide input CSV file(s)!", call. = FALSE)
}
if (length(args) > 1) {
    stop("Command line arguments beyond 1 place will be ignored!",
         call. = FALSE)
}

d <- read.table(args[1], sep = "\t", header = TRUE, fill = TRUE,
                comment.char = "", quote = "\"")

lps <- d[!grepl("\\[EP\\]| - EP|\\[Single\\]| - Single", d$Album), ]
eps <- d[grepl("\\[EP\\]| - EP", d$Album), ]

cat("Don't forget to remove tracks that you don't want captured in the POWER",
    "INDEX calculation that may not be filtered out (e.g. Skits, Credits).\n\n")

## validations
# dirty_tags <- d[!grepl(":", d$Genre) | grepl(" - EP| - Single", d$Album), ]
# if (nrow(dirty_tags) > 0) {
#     cat("The following releases do not have properly tagged genres:\n\n")
#     print(dirty_tags[ , c("Artist", "Album", "Name")],
#           row.names = FALSE)
#     cat("\n")
#     stop("Clean these tags and try again.", call. = FALSE)
# }
yrs <- d %>%
    group_by(Artist, Album) %>%
    summarize(yrs = length(unique(Year)), .groups = "keep") %>%
    select(Artist, Album, yrs) %>%
    as.data.frame
if (any(yrs$yrs > 1)) {
    cat(paste0("The following releases have more than one year denoted across ",
               "the tracks:\n\n"))
    print(yrs[yrs$yrs > 1, c("Artist", "Album")], row.names = FALSE)
    cat("\n")
    stop("Fix the Year tag and try again.", call. = FALSE)
}
check_lps <- lps %>%
    add_count(Album) %>%
    group_by(Album) %>%
    summarize(
        Artist = first(Artist), n = unique(n),
        TotalTime = sum(Time) / 60,
        .groups = "keep"
    ) %>%
    select(Artist, Album, n, TotalTime) %>%
    mutate(invalid = TotalTime < 30 | n < 8) %>%
    as.data.frame
if (any(check_lps$invalid)) {
    cat(paste0("The following releases are not tagged as an EP yet are ",
               "shorter than 30 mins in length or have fewer than 8 ",
               "tracks:\n\n"))
    print(check_lps[check_lps$invalid, c("Artist", "Album")],
          row.names = FALSE)
    cat("\n")
    cat("Ignore and keep going? (Y or N): ")
    input <- file("stdin")
    resp <- readLines(input, 1)
    if (tolower(resp) != "y") {
        stop("Change these Albums to be EPs and try again.", call. = FALSE)
    }
}
check_eps <- eps %>%
    add_count(Album) %>%
    group_by(Album) %>%
    summarize(
        Artist = first(Artist),
        n = unique(n), TotalTime = sum(Time) / 60,
        .groups = "keep"
    ) %>%
    select(Artist, Album, n, TotalTime) %>%
    mutate(invalid = (TotalTime >= 30 & n >= 8) | TotalTime < 10 | n < 3) %>%
    as.data.frame
if (any(check_eps$invalid)) {
    cat(paste0("The following releases are either too long or too short to ",
               "be EPs:\n\n"))
    print(check_eps[check_eps$invalid, c("Artist", "Album")],
          row.names = FALSE)
    cat("\n")
    stop("Fix or remove these EPs and try again.", call. = FALSE)
}
check_deluxe <- unique(c(lps[grepl("Deluxe", lps$Album), "Album"],
                         eps[grepl("Deluxe", eps$Album), "Album"]))
if (length(check_deluxe) > 0){
    cat(paste0("Have you removed Deluxe Edition / Bonus Tracks from the ",
               "following albums?\n\n"))
    cat(check_deluxe, sep = "\n")
    cat("\n")
}

lps <- cleanDupes(lps)
eps <- cleanDupes(eps)

# delete files and images
files <- c(
    list.files("output", "spotify_playlist.txt"), "follow.txt", "unfollow.txt"
)
for (f in files) {
    unlink(file.path("output", f), force = TRUE)
}
unlink("./imgs", recursive = TRUE, force = TRUE)

inputs <- list.files("input", "-Power-Rankings-")
year_types <- c(
    if (nrow(lps)) {
        mapply(list, sort(unique(lps$Year)), "ALBUM", SIMPLIFY = FALSE)
    } else NULL,
    if (nrow(eps)) {
        mapply(list, sort(unique(eps$Year)), "EP", SIMPLIFY = FALSE)
    } else NULL
)

## authorize spotifyR
auth_obj <- auth()
access_token <- auth_obj$access_token

for (yt in year_types) {
    year <- yt[[1]]
    type <- yt[[2]]
    cat(paste0("\n", year, "  -  ", type, "s\n:::::::::::::::\n"))
    ## load data
    pre <- inputs[grepl(type, inputs, ignore.case = TRUE)]
    pre <- pre[
        vapply(pre, function(p) substr(p, 4, 7) == year, FUN.VALUE = logical(1))
    ]
    if (type == "EP") {
        out.name <- "EP_RANKINGS.csv"
        d.add <- eps[eps$Year == year, ]
    } else {
        out.name <- "ALBUM_RANKINGS.csv"
        d.add <- lps[lps$Year == year, ]
    }
    if (length(pre) > 0) {
        suppressWarnings(d.pre <- read.csv(
            file.path("input", pre), stringsAsFactors = FALSE, sep = "\t",
            encoding = "windows-1252",
            colClasses = c(
                "RANK" = "character", "ARTIST" = "character",
                "ALBUM" = "character", "EP" = "character",
                "GENRE" = "character", "POWER<br>INDEX" = "numeric",
                "RATING" = "character", "TREND" = "character"
            )
        ))
        d.pre$POWER.br.INDEX <- as.numeric(gsub(" ", "", gsub(
            "<span id='pilarge'>|</span><span id='pismall'>|</span>",
            "",
            d.pre$POWER.br.INDEX
        )))
    }

    follow <- data.frame()
    for (release in unique(d.add$Album)) {
        rel <- d.add[d.add$Album == release, ]
        power.index <- powerIndex(rel)
        if (type == "ALBUM") {
            if (power.index >= 65.0 || (any(rel$My.Rating > 60) && power.index >= 62.0)) {
                follow.bool <- TRUE
                cat(
                    rel$Artist[1],
                    file = paste0("output/follow.txt"),
                    append = TRUE,
                    sep = "\n"
                )
            } else {
                follow.bool <- FALSE
                cat(
                    rel$Artist[1],
                    file = paste0("output/unfollow.txt"),
                    append = TRUE,
                    sep = "\n"
                )
            }
        } else {
            if (power.index >= 62.0 || (any(rel$My.Rating > 60) && power.index >= 60.0)) {
                follow.bool <- TRUE
                cat(
                    rel$Artist[1],
                    file = paste0("output/follow.txt"),
                    append = TRUE,
                    sep = "\n"
                )
            } else if (power.index < 40.0 || (!any(rel$My.Rating > 40) && power.index < 62.0)) {
                follow.bool <- FALSE
                cat(
                    rel$Artist[1],
                    file = paste0("output/unfollow.txt"),
                    append = TRUE,
                    sep = "\n"
                )
            }
        }
        follow <- rbind(
            follow,
            data.frame(
                Artist = rel$Artist[1],
                Album = release,
                follow.bool = follow.bool
            )
        )
    }

    ## power index and rating
    d.add <- d.add %>%
        group_by(Artist, Album) %>%
        group_map(~ data.frame(
            RANK = "",
            X = "",
            ARTIST = .y$Artist[1],
            RELEASE = .y$Album[1],
            GENRE = parseGenre(.x$Genre[1]),
            POWER.br.INDEX = powerIndex(.x)
        )) %>%
        do.call(rbind, .) %>%
        mutate(RATING = Vectorize(starRating)(POWER.br.INDEX),
               TREND = rep("", length(POWER.br.INDEX)))
    d.add$RELEASE <- gsub(" \\[.*", "", d.add$RELEASE)
    colnames(d.add)[colnames(d.add) == "RELEASE"] <- type

    if (any(is.na(d.pre$RATING))) {
        d.pre$RATING <- Vectorize(starRating)(d.pre$POWER.br.INDEX)
    }

    ## process
    ## #######

    ## add to d.pre (d.new)
    if (length(d.pre) && "TREND" %in% names(d.pre)) {
        d.pre$TREND <- rep("_update_", nrow(d.pre))
    } else if (length(d.pre) && !"TREND" %in% names(d.pre)){
        d.add <- d.add[ , !colnames(d.add) %in% "TREND"]
    }
    if (length(d.pre)) {
        d.new <- rbind(d.pre, d.add, stringsAsFactors = FALSE)
    } else {
        d.new <- d.add
    }

    if (length(d.pre)) {
        ## update any previously existing entries
        common <- dplyr::intersect(
            d.add[ , c("ARTIST", type)],
            d.pre[ , c("ARTIST", type)]
        )
        if (nrow(common)) {
            for (i in 1:nrow(common)) {
                update <- d.new$ARTIST == common$ARTIST[[i]] &
                    d.new[ , type] == common[ , type][[i]]
                update.pre <- which(update & d.new[ , "X"] != "")
                update.add <- which(update & d.new[ , "X"] == "")
                if ("TREND" %in% names(d.new)) {
                    pre_pi <- d.new[update.pre, "POWER.br.INDEX"]
                    add_pi <- d.new[update.add, "POWER.br.INDEX"]
                    if (pre_pi > add_pi) {
                        d.new[update.pre, "TREND"] <- TREND.DN
                    } else if (pre_pi < add_pi) {
                        d.new[update.pre, "TREND"] <- TREND.UP
                    } else {
                        d.new[update.pre, "TREND"] <- TREND.NO
                    }
                }
                d.new[update.pre, "POWER.br.INDEX"] <- d.new[
                    update.add, "POWER.br.INDEX"
                ]
                d.new[update.pre, "GENRE"] <- d.new[update.add, "GENRE"]
                d.new <- d.new[-update.add, ]
            }
        }
    }

    ## sort and re-rank and clean-up
    d.sorted <- d.new[order(d.new$POWER.br.INDEX, decreasing = TRUE), ]
    ranks <- rank(-(as.numeric(d.sorted$POWER.br.INDEX)), ties.method = "min")
    ranks.ties <- sapply(1:length(ranks), function(i) {
        if (duplicated(ranks)[i]) {
            return (paste0("T", ranks[i]))
        } else if (i != length(ranks) && duplicated(ranks)[i + 1]) {
            return (paste0("T", ranks[i]))
        } else return (ranks[i])
    })
    d.sorted$RANK <- ranks.ties
    d.sorted$POWER.br.INDEX <- as.numeric(d.sorted$POWER.br.INDEX)

    ## calculate and determine trends
    if ("TREND" %in% names(d.sorted) && !all(d.sorted$TREND == "")) {
        ## previous index scores
        d1 <- d.pre[!is.na(d.pre$POWER.br.INDEX), ]
        ## all index scores, including new
        d2 <- as.numeric(d.sorted$POWER.br.INDEX)
        if (nrow(d.pre) != 1 && !any(d.pre$POWER.br.INDEX == "")) {
            cuts <- if (length(d2) < 50) 0.25 else 0.2
            cuts <- if (length(d2) > 80) 0.10 else cuts
            cut1 <- .bincode(
                d1$POWER.br.INDEX,
                quantile(d1$POWER.br.INDEX, probs = seq(0, 1, cuts)),
                include.lowest = TRUE
            )
            cut2 <- .bincode(
                d1$POWER.br.INDEX,
                quantile(d2, probs = seq(0, 1, cuts), na.rm = TRUE),
                include.lowest = TRUE
            )
            ## compare these two cuts takes albums previous in power ranking
            ## and looks at where they land in the decile compares them to where
            ## they land using the new decile with the new album entries if an
            ## album has a lower value in the cut output on the second than the
            ## first, it trends down, and vice-versa.
            diffs <- cut2 - cut1
            d.diffs <- cbind(d.pre, diffs)
            for (i in 1:nrow(d.diffs)) {
                if (is.na(diffs[i])) {
                    trend <- TREND.NEW
                } else if (diffs[i] == 0) {
                    trend <- TREND.NO
                } else if (diffs[i] < 0) {
                    trend <- TREND.DN
                } else if (diffs[i] > 0) {
                    trend <- TREND.UP
                }
                matched <- which(d.sorted$ARTIST == d.pre$ARTIST[[i]] &
                                 d.sorted$X == d.pre$X[[i]])
                if (d.sorted$TREND[[matched]] == "_update_") {
                    d.sorted$TREND[[matched]] <- trend
                }
            }
        } else {
            keep <- d.sorted$TREND != "_update_" &
                !is.na(d.sorted$POWER.br.INDEX)
            d.sorted <- d.sorted[keep, ]
        }
    } else if ("TREND" %in% names(d.sorted) && all(d.sorted$TREND == "")) {
        d.sorted$TREND <- TREND.NEW
    }

    ## parser
    res <- lapply(1:nrow(d.sorted), function(i) {
        parseRankings(i, d.sorted, year, type, access_token)
    })
    ## un/follow
    auth_token <- auth_obj$auth_token
    cat("\n")
    for (i in 1:nrow(follow)) {
        artist <- follow[i, "Artist"]
        artists <- spotifyR:::search_spotify(
            decodeString(artist),
            type = "artist",
            market = "US",
            authorization = access_token
        )
        artist.id <- NULL
        if ("name" %in% names(artists) &&
            length(artists$name)) {
            for (j in 1:length(artists$name)) {
                ## find first exact match
                poss <- matchPossibilities(artist)
                if (stringi::stri_trans_tolower(artists$name[j]) %in% poss) {
                    artist.id <- artists$id[j]
                    break
                }
            }
        }
        fllw <- follow$follow.bool[[i]]
        if (is.null(artist.id)) {
            action <- if (fllw) "follow" else "unfollow"
            warning(
                paste(
                    "You will need to manually", action, artist, "in Spotify."
                ),
                call. = FALSE, immediate. = TRUE
            )
        } else {
            auth_token <- updateFollowing(artist, artist.id, fllw, auth_token)
        }
    }
    d.out <- data.frame(
        do.call(rbind, res),
        stringsAsFactors = FALSE
    )

    ## export to CSV
    names(d.out)[which(names(d.out) == "X")] <- ""
    names(d.out)[which(names(d.out) == "POWER.br.INDEX")] <- "POWER<br>INDEX"
    write.csv(
        format(d.out),
        file = file.path("output", paste0(year, "_", out.name)),
        row.names = FALSE
    )

    d.pre <- NULL
    d.add <- NULL
}

cat("\n")
warning(
    paste0(
        "Check 'unfollow.txt' to be certain you want to unfollow those ", 
        "artists in Spotify."
    ),
    call. = FALSE, immediate. = TRUE
)