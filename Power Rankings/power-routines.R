## "static" vars
LINK.PRE <- "<a href='"
LINK.MID <- "' class='circle-thumbnail'><div class='circlecrop' style=background-image:url('http://afireintheattic.com/wp-content/uploads/"
LINK.END <- ".jpg')></div></a>"
SCORE.PRE <- "<span id='pilarge'>"
SCORE.MID <- "</span><span id='pismall'>"
SCORE.END <- "</span>"
TREND.NO <- "<div class='no_change'>--</span>"
TREND.UP <- "<img src='http://afireintheattic.com/wp-content/uploads/up_gr_40.png' width='25' height='25' class='center'/>"
TREND.DN <- "<img src='http://afireintheattic.com/wp-content/uploads/down_rd_40.png' width='25' height='25' class='center'/>"
TREND.NEW <- "<div class='new_entry'>NEW<br>ENTRY</span>"
IMG.FIRE <- "<img class='imgfire'>"
FIRE.HALF <- "<img class='firehalf'>"

getShorty <- function(vec) {
    shorties <- vec[!grepl("&|,", vec)]
    if (length(shorties) == 0) {
        shortest <- names(which.min(vapply(vec, nchar, numeric(1))))[1]
    } else {
        for (shorty in shorties) {
            shortest <-  names(which.max(
                vapply(shorties, function(a) sum(grepl(a, vec)), numeric(1))
            ))[1]
        }
    }
    return(shortest)
}
isOverlap <- function(vec) {
    x <- strsplit(vec, " |\\, ")
    overlap <- sum(vapply(seq_along(x), function(i) {
        return(any(vapply(
            Vectorize(intersect)(x[i], x[!seq_along(x) %in% i]),
            length,
            numeric(1)
        ) > 0))
    }, logical(1))) > (length(vec) / 2)
    return(overlap)
}
isNearComplete <- function(vec) {
    shortest <- getShorty(vec)
    return((sum(grepl(shortest, vec)) / length(vec)) > 0.80)
}

cleanDupes <- function(df) {
    grpd <- df %>%
        add_count(Artist, Album, Genre) %>%
        group_by(Artist, Album, Genre) %>%
        summarize(n = unique(n), .groups = "keep") %>%
        ungroup () %>%
        select(Artist, Album) %>%
        as.data.frame
    dupes <- grpd[duplicated(grpd$Album), "Album"]
    for (dupe in dupes) {
        duped <- grpd[grpd$Album == dupe, ]
        shortest <- getShorty(duped$Artist)
        if (isOverlap(duped$Artist) || isNearComplete(duped$Artist)) {
            ## if there are dupes and they are the main artist name with
            ## featuring artist names, then rename to the main artist
            df[df$Album == dupe & df$Artist != shortest, "Artist"] <- shortest
        }
    }
    return(df)
}

powerMath <- function(ratings) {
    remap <- c("20" = 1, "40" = 2, "60" = 3, "80" = 4, "100" = 5)
    weights <- c("1" = 1.0, "2" = 1.2, "3" = 1.0, "4" = 1.2, "5" = 1.0)
    ratings <- vapply(ratings, function(a) {
        return(remap[[as.character(a)]])
    }, numeric(1))
    ratings_wtd <- vapply(ratings, function(a) {
        return(weights[[as.character(a)]])
    }, numeric(1)) * ratings
    ## min possible score: (mean of 1-star)
    mn1 <- 1.0
    ## max possible score: Radiohead "OK Computer"
    mx1 <- 5.662521
    mn2 <- -1.0
    mx2 <- -0.125
    ## calculate mean rating
    mean_album <- mean(ratings)
    ## calculate standard deviation of ratings
    stddev <- sd(ratings)
    if (isTRUE(stddev == 0)) {
        ## this is a standard deviation barely over 0 (as in, all ratings are
        ## the same except for one song being offset by 1)
        stddev <- 0.25
    }
    ## get album mean not counting 3s
    if (all(ratings == 3)) {
        adj_mean <- 3.0
    } else {
        adj_mean <- mean(ratings_wtd[ratings_wtd != 3])
    }
    ## get proportion of 4s and 5s
    prop4or5 <- sum(ratings > 3) / length(ratings)
    ## calculate adjustments
    adj1 <- (adj_mean - 3) * prop4or5
    adj2 <- adj1 + sum(ratings >= 3) * 0.03
    score <- mean_album + adj2
    ## standard deviation adjustment
    if (prop4or5 == 0) {
        adj_sd <- stddev * 0.05
    } else {
        adj_sd <- stddev * prop4or5 / length(ratings)
    }
    score <- score - adj_sd
    ## scale
    scaled_score <- (score - mn1) / (mx1 - mn1)
    ## transform (curves the linear scores to inflate higher scores and reduce
    ## lower)
    transformed_score <- -1 * (8 ^ (-1 * scaled_score))
    ## scale
    scaled_score <- (transformed_score - mn2) / (mx2 - mn2)
    x <- (round(scaled_score * 1000)) / 1.0
    if (x > 1000) x <- 1000 else if (x < 0) x <- 1
    return(x / 10)
}

powerIndex <- function(rows) {
    ratings <- rows$My.Rating
    ## don't consider tracks with Time under 2 minutes unless:
    ## - they improve the powerMath score
    ## - the album has a mean track Time under 2:15 or more than 40% of its
    ##   tracks under 2 minutes, in which case don't consider tracks under 1 min
    ##   unless they improve the powerMath score
    mean_time <- mean(rows$Time / 60)
    prop_under2 <- sum(rows$Time < 120) / nrow(rows)
    if (mean_time < 2.25 || prop_under2 > 0.40) {
        score1 <- powerMath(ratings[rows$Time >= 60 | ratings >= 60.0])
        score2 <- powerMath(ratings[rows$Time >= 60])
    } else {
        score1 <- powerMath(ratings[rows$Time >= 120 | ratings >= 60.0])
        score2 <- powerMath(ratings[rows$Time >= 120])
    }
    return(max(score1, score2))
}

starRating <- function(x) {
    if (x >= 96.5) {
        ## 5.0 STAR ALBUMS: from [low] The National's "High Violet" to [high]
        ## Radiohead's "OK Computer"
        star_rating <- 5
    } else if (x >= 89.0 && x < 96.5) {
        ## 4.5 STAR ALBUMS: from [low] Fall Out Boy's "Folie À Deux" to [high]
        ## _________?
        star_rating <- 4.5
    } else if (x >= 75.0 && x < 89.0) {
        ## 4 STAR ALBUMS: from [low] _________? to [high] _________?
        star_rating <- 4
    } else if (x >= 69.0 && x < 75.0) {
        ## 3.5 STAR ALBUMS: from [low] St. Lucia's "Matter" to [high] The
        ## 1975's "I Like It When You Sleep..."
        star_rating <- 3.5
    } else if (x >= 62.5 && x < 69.0) {
        ## 3.0 STAR ALBUMS: from [low] _________? to [high] Haywyre's "Two
        ## Fold, Pt. 2"
        star_rating <- 3
    } else if (x >= 42.0 && x < 62.5) {
        ## 2.5 STAR ALBUMS: from [low] _________? to [high] Drake's "Views"?
        star_rating <- 2.5
    } else if (x > 32.5 && x < 42.0) {
        ## 2.0 STAR ALBUMS: from [low] _________? to [high] Greyhounds' "Change
        ## Of Pace"?
        star_rating <- 2
    } else if (x > 23.5 && x <= 32.5) {
        ## 1.5 STAR ALBUMS: from [low] Madonna's "Hard Candy" to [high] The
        ## Rubens' "Hoops"
        star_rating <- 1.5
    } else if (x >= 10.0 && x <= 23.5) {
        ## 1.0 STAR ALBUMS: from [low] _________? to [high] _________?
        star_rating <- 1
    } else if (x < 10.0) {
        ## 0.5 STAR ALBUMS: from lowest possible rated album to [high]
        ## _________?
        star_rating <- 0.5
    }
    return(star_rating)
}

releaseSlug <- function(text) {
    text <- gsub("\\(", "", text)
    text <- gsub("\\)", "", text)
    text <- gsub("&", "", text)
    text <- gsub("\\.", "", text)
    text <- gsub(",", "", text)
    text <- gsub("\\[", "", text)
    text <- gsub("\\]", "", text)
    text <- gsub("\\'", "", text)
    text <- gsub("\\s", "", text)
    text <- gsub("\\:", "", text)
    text <- gsub("\\/", "", text)
    text <- gsub("\\?", "", text)
    text <- gsub("\\!", "", text)
    tolower(text)
}

getter <- function(url, query, ...) {
    response <- httr::GET(url = url, query = query, ...)
    if (httr::status_code(response) == 429) {
        print("Too many requests. Waiting...")
    }
}

getTopSong <- function(artist, album, access_token, year, type) {
    if (grepl('open.spotify.com', album)) {
        album <- gsub('(.*album/)|(\\?.*|\'.*)', '', album)
    }
    tryCatch({
        tracks <- spotifyr::get_album_tracks(
            album, authorization = access_token
        )
        tracks <- spotifyr::get_tracks(tracks$id)
        track <- tracks[
            intersect(
                grep("US", tracks$available_markets),
                which.max(tracks$popularity)
            ),
            "uri"
        ]
        if (length(trimws(track)) == 0) {
            cat("What is the URL of the release? ")
            album <- readLines(con = "stdin", 1)
            album <- gsub("https://open.spotify.com/album/", "", album)
            album <- strsplit(album, "\\?")[[1]][1]
            tracks <- spotifyr::get_album_tracks(
                album, authorization = access_token
            )
            tracks <- spotifyr::get_tracks(tracks$id)
            track <- tracks[
                intersect(
                    grep("US", tracks$available_markets),
                    which.max(tracks$popularity)
                ),
                "uri"
            ]
            if (length(trimws(track)) == 0) {
                stop() ## send to error catch if still empty
            }
        }
        cat(
            track,
            file = paste0(
                "output/", year, "_", type,
                "_spotify_playlist.txt"
            ),
            append = TRUE,
            sep = "\n"
        )
    }, error = function(e) {
        manualURI(artist, album, year, type)
    })
}

manualURI <- function(artist, release, year, type, curr_URI = NULL) {
    cat("What is the URL of the most popular song on the release? ")
    cat("(Enter song title or local link if not available on Spotify): ")
    track <- readLines(con = "stdin", 1)
    if (length(track) < 1 && !is.null(curr_URI)) {
        track <- curr_URI
    } else if (grepl("https://open.spotify.com/track/", track)) {
        track <- gsub("https://open.spotify.com/track/", "", track)
        track <- strsplit(track, "\\?")[[1]][1]
        track <- paste0("spotify:track:", track)
    } else if (!grepl("spotify:track:", track) &&
               !grepl("open.spotify.com", track)) {
        track <- paste0(
            "https://open.spotify.com/local/",
            gsub(" ", "%20", artist), "/",
            gsub(" ", "%20", release), "/",
            gsub(" ", "%20", track)
        )
    }
    cat(
        track,
        file = paste0(
            "output/", year, "_", type,
            "_spotify_playlist.txt"
        ),
        append = TRUE,
        sep = "\n"
    )
}

manualURL <- function() {
    cat("What is the URL of the release? ")
    cat("(Enter URL to link from image if not available on Spotify): ")
    release.url <- readLines(con = "stdin", 1)
    warning("You will need to download the release artwork manually.",
            call. = FALSE, immediate. = TRUE)
    return(release.url)
}

decodeString <- function(string, toLower = TRUE) {
    if (toLower)
        stringi::stri_trans_general(
            stringi::stri_trans_tolower(string),
            "latin-ascii"
        )
    else
        stringi::stri_trans_general(
            string,
            "latin-ascii"
        )
}

matchPossibilities <- function(string) {
    decoded <- decodeString(string)
    native <- stringi::stri_enc_tonative(
        stringi::stri_trans_tolower(string)
    )
    lower <- tolower(string)
    ampersand <- gsub("and", "&", tolower(string))
    and <- gsub("&", "and", tolower(string))
    nocommas <- gsub(",", "", tolower(string))
    return(c(
        decoded,
        native,
        lower,
        ampersand,
        and,
        nocommas
    ))
}

## add new entries to previous power rankings, using static vars
parseRankings <- function(i, df, year, type, follow, config, access_token) {
    cat("\n")
    artist <- df$ARTIST[[i]]
    print(artist)
    artists <- NULL
    while (is.null(artists)) {
        artists <- spotifyr:::search_spotify(
            artist,
            type = "artist",
            market = "US",
            authorization = access_token
        )
        if (is.null(artists)) Sys.sleep(5)
    }
    if (!nchar(df$X[[i]])) {
        out <- findEntry(artists, df[i, ], year, type,
                         trend = "TREND" %in% names(df), follow = follow,
                         config = config, access_token = access_token)
    } else {
        out <- findEntry(artists, df[i, ], year, type,
                         trend = "TREND" %in% names(df), updateOnly = TRUE,
                         follow = follow, config = config,
                         access_token = access_token)
    }
    return(out)
}

findEntry <- function(artists, entry, year, type, firstAttempt = TRUE,
                      updateOnly = FALSE, artistIter = 1, trend = TRUE,
                      follow, config, access_token) {
    artist <- entry$ARTIST
    release <- entry[[type]]
    release.trunc <- releaseSlug(release)
    artist.id <- NULL
    if (!is.na(suppressWarnings(as.numeric(entry$POWER.br.INDEX)))) {
        if (is.na(entry$RATING) || entry$RATING == "") {
            entry$RATING <- starRating(as.numeric(entry$POWER.br.INDEX))
        }
        pi <- as.character(entry$POWER.br.INDEX)
        big <- strsplit(pi, "\\.")[[1]][1]
        small <- strsplit(pi, "\\.")[[1]][2]
        if (is.na(small)) small <- 0
        pi <- paste0(SCORE.PRE, big, SCORE.MID, ". ", small, SCORE.END)
    } else  if (grepl(SCORE.PRE, entry$POWER.br.INDEX)) {
        pi <- entry$POWER.br.INDEX
    } else {
        print(entry$POWER.br.INDEX)
        stop("Something is wrong with this entry's POWER.br.INDEX.",
             call. = FALSE)
    }
    if (!is.na(suppressWarnings(as.numeric(entry$RATING)))) {
        fire_rating <- paste(
            rep(IMG.FIRE, floor(as.numeric(entry$RATING))), collapse = ""
        )
        if (as.numeric(entry$RATING) %% 1 == 0.5) {
            fire_rating <- paste0(fire_rating, FIRE.HALF)
        }
    } else if (grepl("<img class", entry$RATING)) {
        fire_rating <- entry$RATING
    } else {
        print(entry$RATING)
        stop("Something is wrong with this entry's RATING.", call. = FALSE)
    }
    old.entry <- data.frame(
        entry$RANK,
        entry$X,
        entry$ARTIST,
        entry[[4]],
        entry$GENRE,
        pi,
        fire_rating,
        if ("TREND" %in% names(entry)) entry$TREND else TREND.NO,
        stringsAsFactors = FALSE
    )
    if (!trend) old.entry <- old.entry[ , -8]
    old.entry <- setNames(old.entry, names(entry))
    if ("name" %in% names(artists) &&
        length(artists$name) > 0 &&
        artistIter <= length(artists$name)) {
        for (j in artistIter:length(artists$name)) {
            ## find first exact match
            poss <- matchPossibilities(artist)
            if (stringi::stri_trans_tolower(artists$name[j]) %in% poss) {
                artist.id <- artists$id[j]
                break
            }
        }
    }
    if (firstAttempt && is.null(artist.id)) {
        artists <- spotifyr:::search_spotify(
            decodeString(artist),
            type = "artist",
            market = "US",
            authorization = access_token
        )
        return(findEntry(
            artists,
            entry,
            year,
            type,
            firstAttempt = FALSE,
            updateOnly = updateOnly,
            trend = trend,
            follow = follow,
            config = config,
            access_token = access_token
        ))
    } else if (is.null(artist.id) && artistIter == 1) {
        print(release)
        if (nchar(entry$X) > 0) {
            ## if not a new entry, use previous X
            x <- entry$X
            getTopSong(artist, x, access_token, year, type)
        } else {
            warning(
                paste0("Artist '", artist,
                       "' not found. You will need to complete ",
                       "the entry manually."),
                call. = FALSE,
                immediate. = TRUE
            )
            warning(
                paste0("Also manually follow the artist."),
                call. = FALSE,
                immediate. = TRUE
            )
            x <- manualURL()
            x <- paste0(LINK.PRE, x, LINK.MID, release.trunc, LINK.END)
            manualURI(artist, release, year, type)
            if (updateOnly) return(old.entry)
        }
        new.entry <- data.frame(
            entry$RANK,
            x,
            artist,
            release,
            entry$GENRE,
            pi,
            fire_rating,
            TREND.NEW,
            stringsAsFactors = FALSE
        )
        if (!trend) new.entry <- new.entry[ , -8]
        return(setNames(new.entry, names(entry)))
    } else if (is.null(artist.id) && artistIter > 1) {
        print(release)
        if (nchar(entry$X) > 0) {
            ## if not a new entry, use previous X
            x <- entry$X
            getTopSong(artist, x, access_token, year, type)
        } else {
            warning(
                paste0("Release '", release,
                       "' not found. You will need to complete ",
                       "the entry manually."),
                call. = FALSE,
                immediate. = TRUE
            )
            warning(
                paste0("Also manually follow the artist."),
                call. = FALSE,
                immediate. = TRUE
            )
            x <- manualURL()
            x <- paste0(LINK.PRE, x, LINK.MID, release.trunc, LINK.END)
            manualURI(artist, release, year, type)
            if (updateOnly) return(old.entry)
        }
        new.entry <- data.frame(
            entry$RANK,
            x,
            artist,
            release,
            entry$GENRE,
            pi,
            fire_rating,
            TREND.NEW,
            stringsAsFactors = FALSE
        )
        if (!trend) new.entry <- new.entry[ , -8]
        return(setNames(new.entry, names(entry)))
    }
    releases <- NULL
    while (is.null(releases)) {
        tryCatch({
            releases <- spotifyr:::get_artist_albums(
                artist.id, market = "US", authorization = access_token
            )
        }, error = function(e) {
            releases <<- NULL
        })
        if (is.null(releases)) Sys.sleep(5)
    }
    if ("name" %in% names(releases) && length(releases$name) > 0) {
        for (k in 1:length(releases$name)) {
            possibilities <- matchPossibilities(release)
            release.iter <- stringi::stri_trans_tolower(releases$name[k])
            poss <- any(sapply(possibilities, function(x) {
                return(x == release.iter)
            }))
            if (release.iter %in% possibilities || poss) {
                release.id <- releases$id[k]
                tryCatch({
                    tracks <- spotifyr:::get_album_tracks(
                        release.id, authorization = access_token
                    )
                }, error = function(e) {
                    tracks <<- NULL
                })
                if (length(tracks$track_number) < 3) ## it's a single
                    next
                if ("US" %in% unlist(tracks$available_markets)) {
                    print(release)
                    release.url <- releases$external_urls.spotify[k]
                    dir.create(file.path("./imgs"), showWarnings = FALSE)
                    if (!updateOnly) {
                        download.file(
                            releases$images[k][[1]]$url[1],
                            file.path(
                                "./imgs/", paste0(release.trunc, ".png")
                            ),
                            quiet = TRUE
                        )
                    }
                    tryCatch({
                        tracks.top <- spotifyr:::get_artist_top_tracks(
                            artist.id,
                            market = "US",
                            authorization = access_token
                        )
                        ## find top track from album
                        track <- as.character(
                            tracks.top[
                                tracks.top$album.id %in% release.id,
                                "uri"
                            ][1]
                        )
                    }, error = function(e) {
                        track <<- NULL
                    })
                    if (is.null(track) || is.na(track)) {
                        ## no track from this album is in the artist's top 10
                        pops <- sapply(tracks$id, function(x) {
                            spotifyr:::get_track(
                                x,
                                market = "US",
                                authorization = access_token
                            )$popularity
                        })
                        track <- tracks$uri[[
                            which(pops %in% max(pops, na.rm = TRUE))[1]
                        ]]
                    }
                    if (is.na(track) || is.null(track)) {
                        stop("Something went wrong...")
                    }
                    cat(
                        track,
                        file = paste0(
                            "output/", year, "_", type,
                            "_spotify_playlist.txt"
                        ),
                        append = TRUE,
                        sep = "\n"
                    )
                    if (length(follow)) {
                        updateFollowing(artist.id, follow, config)
                    }
                    if (updateOnly) return(old.entry)
                    new.entry <- data.frame(
                        entry$RANK,
                        paste0(LINK.PRE, release.url, LINK.MID,
                               release.trunc, LINK.END),
                        artist,
                        release,
                        entry$GENRE,
                        pi,
                        fire_rating,
                        TREND.NEW,
                        stringsAsFactors = FALSE
                    )
                    if (!trend) new.entry <- new.entry[ , -8]
                    return(setNames(new.entry, names(entry)))
                }
            }
        }
    }

    ## try next artist in list
    return(findEntry(
        artists,
        entry,
        year,
        type,
        firstAttempt,
        updateOnly,
        artistIter = artistIter + 1,
        trend = trend,
        follow = follow,
        config = config,
        access_token = access_token
    ))
}

parseGenre <- function(genre) {
    if (grepl("\\[", genre)) {
        genre <- gsub(" \\[.*", "", genre)
    }
    if (!grepl(" : ", genre)) {
        return(genre)
    }
    if (grepl("^[Pop : ]", genre)) {
        return("Pop")
    } else if (grepl("^[Classical : ]", genre)) {
        return("Classical")
    } else if (genre == "Electronic : Experimental") {
        return("Electronic")
    } else {
        return(strsplit(genre, " : ")[[1]][2])
    }
}

updateFollowing <- function(artist.id, follow, config) {
    reticulate::use_python("/usr/local/bin/python3")
    spotipy <- reticulate::import("spotipy")
    spauth <- spotipy$SpotifyOAuth(
        client_id = config[["SPOTIFY_CLIENT_ID"]],
        client_secret = config[["SPOTIFY_CLIENT_SECRET"]],
        redirect_uri = config[["SPOTIFY_REDIRECT_URI"]],
        scope = config[["SPOTIFY_SCOPE"]],
        username = config[["SPOTIFY_USERNAME"]]
    )
    sp <- spotipy$Spotify(auth_manager = spauth)
    if (follow) {
        sp$user_follow_artists(list(artist.id))
    } else {
        sp$user_unfollow_artists(list(artist.id))
    }
}