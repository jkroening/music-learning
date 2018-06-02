################################################################################
## Takes a tab-separated csv table (exported from Wordpress TablePress plugin)
## and a comma-separated csv table of updates/additions to make to the table,
## downloads the needed info from Spotify, parses it, combines the tables, sorts
## them and updates the appropriate cells. The exported table can then be
## imported back in to TablePress.
################################################################################

suppressMessages(library(spotifyr))
suppressMessages(library(dplyr))
suppressMessages(library(stringi))

args = commandArgs(trailingOnly = TRUE)

if (length(args) == 0)
    stop("Must provide input CSV file(s)!", call. = FALSE)
if (length(args) == 1)
    warning("New additions to the power rankings will be asked one-by-one via ",
            "prompt.", call. = FALSE, immediate. = TRUE)
if (length(args) > 2)
    stop("Command line arguments beyond 2 places will be ignored!",
         call. = FALSE)

## load data
d.pre <- read.csv(args[1], stringsAsFactors = FALSE, encoding = "windows-1252",
                  sep = "\t")
## if empty d.pre
if (nrow(d.pre) == 0) {
    d.pre <- data.frame(t(matrix(rep("", 7))), stringsAsFactors = FALSE)
    colnames(d.pre) <- c("RANK", "X", "ARTIST", "ALBUM", "GENRE", "POWER.INDEX", "TREND")
}

if (length(args) == 2) {
    d.add <- suppressWarnings(
        read.csv(args[2], stringsAsFactors = FALSE, encoding = "iso-8859-1")
    )
    out <- system(paste("file --mime", args[2]), intern = TRUE)
    # if (any(!stringi::stri_enc_isascii(unlist(d.add))) &&
    #        !grepl("iso-8859", out) && !grepl("unknown-8bit", out))
    #    stop("You probably forgot to save ", args[2], " as a Windows Comma ",
    #         "Separated file!", call. = FALSE)
    d.add$ARTIST <- iconv(d.add$ARTIST, "iso-8859-1", "utf-8")
    d.add$RELEASE <- iconv(d.add$RELEASE, "iso-8859-1", "utf-8")
    d.add <- setNames(
        data.frame(cbind(
            rep("", nrow(d.add))
          , rep("", nrow(d.add))
          , d.add$ARTIST
          , d.add$RELEASE
          , d.add$GENRE
          , d.add$POWER.INDEX
          , if ("TREND" %in% names(d.pre)) rep("", nrow(d.add)) else NULL
        ), stringsAsFactors = FALSE)
      , names(d.pre)
    )
    if (grepl("new_eps.csv", args[2])) {
        out.name <- "EP_RANKINGS.csv"
        RELEASE.TYPE <- "EP"
        colnames(d.pre)[4] <- RELEASE.TYPE
        colnames(d.add)[4] <- RELEASE.TYPE
    } else {
        out.name <- "ALBUM_RANKINGS.csv"
        RELEASE.TYPE = "ALBUM"
    }
}

## delete spotify playlist file
unlink("output/spotify_playlist.txt", force = TRUE)

## "static" vars
LINK.PRE <- "<a href='"
LINK.MID <- "' class='circle-thumbnail'><div class='circlecrop' style=background-image:url('http://afireintheattic.com/wp-content/uploads/"
LINK.END <- ".jpg')></div></a>"
trend.no <- "<div class='no_change'>--</span>"
trend.up <- "<img src='http://afireintheattic.com/wp-content/uploads/up_gr_40.png' width='25' height='25' class='center' />"
trend.dwn <- "<img src='http://afireintheattic.com/wp-content/uploads/down_rd_40.png' width='25' height='25' class='center' />"
TREND.NEW <- "<div class='new_entry'>NEW ENTRY</span>"

## process

## if d.add is not defined, must prompt for all new entries
## TODO later

## add to d.pre (d.new)
if ("TREND" %in% names(d.pre))
    d.pre$TREND <- rep("_update_", nrow(d.pre))
d.new <- rbind(d.pre, d.add, stringsAsFactors = FALSE)

## update any previously existing entries
common <- dplyr::intersect(
    d.add[ , c("ARTIST", RELEASE.TYPE)]
  , d.pre[ , c("ARTIST", RELEASE.TYPE)]
)
if (nrow(common)) {
    for (i in 1:nrow(common)) {
        update.pre <- which(
            d.new$ARTIST == common$ARTIST[[i]] &
                d.new[ , RELEASE.TYPE] == common[ , RELEASE.TYPE][[i]] &
                d.new[ , "X"] != ""
        )
        update.add <- which(
            d.new$ARTIST == common$ARTIST[[i]] &
                d.new[ , RELEASE.TYPE] == common[ , RELEASE.TYPE][[i]] &
                d.new[ , "X"] == ""
        )
        if ("TREND" %in% names(d.new)) {
            if (d.new[update.pre, "POWER.INDEX"] > d.new[update.add, "POWER.INDEX"])
                d.new[update.pre, "TREND"] <- trend.dwn
            else if (d.new[update.pre, "POWER.INDEX"] < d.new[update.add, "POWER.INDEX"])
                d.new[update.pre, "TREND"] <- trend.up
            else d.new[update.pre, "TREND"] <- trend.no
        }
        d.new[update.pre, "POWER.INDEX"] <- d.new[update.add, "POWER.INDEX"]
        d.new[update.pre, "GENRE"] <- d.new[update.add, "GENRE"]
        d.new <- d.new[-update.add, ]
    }
}

## sort and re-rank and clean-up
d.sorted <- d.new[order(d.new$POWER.INDEX, decreasing = TRUE), ]
ranks <- rank(-(as.numeric(d.sorted$POWER.INDEX)), ties.method = "min")
ranks.ties <- sapply(1:length(ranks), function(i) {
    if (duplicated(ranks)[i]) {
        return (paste0("T", ranks[i]))
    } else if (i != length(ranks) && duplicated(ranks)[i + 1]) {
        return (paste0("T", ranks[i]))
    } else return (ranks[i])
})
d.sorted$RANK <- ranks.ties
d.sorted$POWER.INDEX <- as.numeric(d.sorted$POWER.INDEX)

## calculate and determine trends
if ("TREND" %in% names(d.sorted)) {
    d1 <- d.pre[!is.na(d.pre$POWER.INDEX), ] ## previous index scores
    d2 <- as.numeric(d.sorted$POWER.INDEX) ## all index scores, including new

    if (nrow(d.pre) != 1 && d.pre$POWER.INDEX != "") {
        cuts <- if (length(d2) < 50) 0.25 else 0.2
        cuts <- if (length(d2) > 80) 0.10 else cuts

        cut1 <- .bincode(d1$POWER.INDEX,
                         quantile(d1$POWER.INDEX, probs = seq(0, 1, cuts)),
                         include.lowest = TRUE)
        cut2 <- .bincode(d1$POWER.INDEX,
                         quantile(d2, probs = seq(0, 1, cuts), na.rm = TRUE),
                         include.lowest = TRUE)

        ## compare these two cuts takes albums previous in power ranking and looks at
        ## where they land in the decile compares them to where they land using the new
        ## decile with the new album entries if an album has a lower value in the cut
        ## output on the second than the first, it trends down, and vice-versa.
        diffs <- cut2 - cut1
        d.diffs <- cbind(d.pre, diffs)

        for (i in 1:nrow(d.diffs)) {
            if (is.na(diffs[i]))
                trend <- TREND.NEW
            else if (diffs[i] == 0)
                trend <- trend.no
            else if (diffs[i] < 0)
                trend <- trend.dwn
            else if (diffs[i] > 0)
                trend <- trend.up
            matched <- which(d.sorted$ARTIST == d.pre$ARTIST[[i]] &
                                 d.sorted$X == d.pre$X[[i]])
            if (d.sorted$TREND[[matched]] == "_update_")
                d.sorted$TREND[[matched]] <- trend
        }
    } else {
        d.sorted <- d.sorted[d.sorted$TREND != "_update_" & !is.na(d.sorted$POWER.INDEX), ]
    }
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
    tolower(text)
}

## get_response_content <- function(response) {
##     ## print("-------- NEW ONE --------") print(response)
##     ## print(content(response)) print(status_code(response))
##     ## print(str(response))
##     if (httr::status_code(response) == 429) browser()
##     if(!httr::status_code(response) %in% c(200,201,204)) {
##         print(httr::content(response, as = "text"))
##         stop(paste(
##             '\nError Code: '
##           , httr::content(response)$error$status
##           , '\n'
##           , httr::content(response)$error$message
##         ))
##     }
##     # Otherwise, return content
##     httr::content(response)
## }
## assignInNamespace("get_response_content", get_response_content, ns = "spotifyr")

## get_track <- function(id) {
##     tracks_url <- paste0(BASE_URL, '/v1/tracks/')
##     search <- httr::GET(url = paste0(tracks_url, id),
##                   httr::add_headers(Authorization=paste('Bearer',SPOTIFY_ACCESS_TOKEN)))
##     get_response_content(search)
## }

## search <- function(q, type, ...) {
##     search_url <- paste(BASE_URL, '/v1/search', sep = '')
##     response <- httr::GET(url = search_url,
##                     query=list(q=q,type=type,...),
##                     httr::add_headers(Authorization=paste('Bearer',SPOTIFY_ACCESS_TOKEN)))
##     get_response_content(response)
## }
## ## assignInNamespace("search", search, ns = getNamespace("spotifyr")

## get_artist_toptracks <- function(id, country, ...) {
##   search <- httr::GET(url = paste(ARTISTS_URL, id, '/top-tracks', sep = ''),
##                 query=list(country=country),
##                 httr::add_headers(Authorization=paste('Bearer',SPOTIFY_ACCESS_TOKEN)))
##   get_response_content(search)
## }
## assignInNamespace("get_artist_toptracks", get_artist_toptracks, ns = "spotifyr")

## get_album_tracks <- function(id, ...) {
##     search <- httr::GET(url = paste(ALBUMS_URL, id, '/', 'tracks', sep = ''),
##                         query = list(...),
##                 httr::add_headers(Authorization=paste('Bearer',SPOTIFY_ACCESS_TOKEN)))
##   get_response_content(search)
## }
## assignInNamespace("get_album_tracks", get_album_tracks, ns = "spotifyr")

## get_artist_albums <- function(id, ...) {
##   search <- httr::GET(url = paste(ARTISTS_URL, id, '/albums', sep = ''),
##                 query=list(...),
##                 httr::add_headers(Authorization=paste('Bearer',SPOTIFY_ACCESS_TOKEN)))
##   get_response_content(search)
## }
## assignInNamespace("get_artist_albums", get_artist_albums, ns = "spotifyr")

getter <- function(url, query, ...) {
    response <- httr::GET(url = url, query = query, ...)
    if (status_code(response) == 429) {
        print("Too many requests. Waiting...")

    }
}

manualURI <- function(artist, release) {
    cat("What is the Spotify URI of the most popular song on the release? ")
    cat("(Enter song title or local link if not available on Spotify): ")
    track <- readLines(con = "stdin", 1)
    if (!grepl("spotify:track:", track) && !grepl("open.spotify.com", track))
        track <- paste0(
            "https://open.spotify.com/local/"
          , gsub(" ", "%20", artist), "/"
          , gsub(" ", "%20", release), "/"
          , gsub(" ", "%20", track)
        )
    cat(track, file = "output/spotify_playlist.txt", append = TRUE, sep = "\n")
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
            stringi::stri_trans_tolower(string)
          , "latin-ascii"
        )
    else
        stringi::stri_trans_general(
            string
          , "latin-ascii"
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
        decoded
      , native
      , lower
      , ampersand
      , and
      , nocommas
    ))
}

## add new entries to previous power rankings, using static vars
parseRankings <- function(i, df) {
    artist <- df$ARTIST[[i]]
    cat("\n")
    ## print(decodeString(artist, toLower = FALSE))
    artists <- NULL
    while (is.null(artists)) {
        artists <- spotifyr::search_spotify(artist, type = 'artist')$artists$items
        if (is.null(artists)) Sys.sleep(5)
    }
    if (!nchar(df$X[[i]])) {
        out <- findEntry(artists, df[i, ], trend = "TREND" %in% names(df))
        return(out)
    } else {
        findEntry(artists, df[i, ], topTrackOnly = TRUE)
        return(df[i, ])
    }
}

findEntry <- function(artists, entry, firstAttempt = TRUE, topTrackOnly = FALSE, artistIter = 1, trend = TRUE) {
    artist <- entry$ARTIST
    release <- entry[[RELEASE.TYPE]]
    release.trunc <- releaseSlug(release)
    artist.id <- NULL
    if (length(artists) && artistIter <= length(artists)) {
        for (j in artistIter:length(artists)) {
            ## find first exact match
            possibilities <- matchPossibilities(artist)
            if (stringi::stri_trans_tolower(artists[[j]]$name) %in% possibilities) {
                artist.id <- artists[[j]]$id
                break
            }
        }
    }
    if (firstAttempt && is.null(artist.id)) {
        artists <- spotifyr::search_spotify(
            decodeString(artist),
            type = 'artist'
        )$artists$items
        return(findEntry(
            artists
          , entry
          , firstAttempt = FALSE
          , topTrackOnly = topTrackOnly
        ))
    } else if (is.null(artist.id) && artistIter == 1) {
        warning("Artist '", artist, "' not found. You will need to complete ",
                "the entry manually.", call. = FALSE, immediate. = TRUE)
        manualURI(artist, release)
        if (topTrackOnly) return(NULL)
        new.entry <- data.frame(
            entry$RANK
          , paste0(LINK.PRE, manualURL(), LINK.MID,
                   release.trunc, LINK.END)
          , artist
          , release
          , entry$GENRE
          , entry$POWER.INDEX
          , TREND.NEW
          , stringsAsFactors = FALSE
        )
        if (!trend) new.entry <- new.entry[ , -7]
        return(setNames(new.entry, names(entry)))
    } else if (is.null(artist.id) && artistIter > 1) {
        warning("Release '", release, "' not found. You will need to complete ",
                "the entry manually.", call. = FALSE, immediate. = TRUE)
        manualURI(artist, release)
        if (topTrackOnly) return(NULL)
        new.entry <- data.frame(
            entry$RANK
          , paste0(LINK.PRE, manualURL(), LINK.MID,
                   release.trunc, LINK.END)
          , artist
          , release
          , entry$GENRE
          , entry$POWER.INDEX
          , TREND.NEW
          , stringsAsFactors = FALSE
        )
        if (!trend) new.entry <- new.entry[ , -7]
        return(setNames(new.entry, names(entry)))
    }
    releases <- spotifyr:::get_artist_albums(artist.id)$items
    if (length(releases)) {
        for (k in 1:length(releases)) {
            possibilities <- matchPossibilities(release)
            release.iter <- stringi::stri_trans_tolower(releases[[k]]$name)
            if (release.iter %in% possibilities ||
                    any(sapply(possibilities, function(x) grepl(x, release.iter)))) {
                if ("US" %in% unlist(releases[[k]]$available_markets)) {
                    print(release)
                    release.id <- releases[[k]]$id
                    tracks <- spotifyr:::get_album_tracks(release.id)$items
                    if (length(tracks) < 2) ## it's a single
                        next
                    release.url <- releases[[k]]$external_urls
                    dir.create(file.path("./imgs"), showWarnings = FALSE)
                    if (!topTrackOnly)
                           download.file(releases[[k]]$images[[1]]$url,
                                         file.path("./imgs/",
                                                   paste0(release.trunc, ".png")),
                                         quiet = TRUE)
                    tryCatch({
                        tracks.top <- spotifyr:::simplify_result(
                            spotifyr:::get_artist_toptracks(artist.id, country = "US")
                          , type = "songs"
                        )
                        ## find top track from album
                        track <- as.character(
                            tracks.top[tracks.top$album.id %in% release.id, "uri"][1]
                        )
                    }, error = function(e) {
                        track <<- NULL
                    })
                    if (is.null(track)) {
                        tmp <- spotifyr:::get_artist_toptracks(artist.id, country = "US")
                        album.idx <- which(sapply(
                            tmp$tracks,
                            function(y) y$album$id == release.id
                        ))[1]
                        track <- tmp$tracks[[album.idx]]$uri
                    }
                    if (is.null(track) || is.na(track)) {
                        ## no track from this album is in the artist's top 10
                        pops <- sapply(tracks, function(x) {
                            get_track(x$id)$popularity
                        })
                        track <- tracks[[which(pops %in% max(pops, na.rm = TRUE))[1]]]$uri
                    }
                    if (is.na(track) || is.null(track)) stop("something went wrong...")
                    cat(track, file = "output/spotify_playlist.txt", append = TRUE, sep = "\n")
                    if (topTrackOnly) return(NULL)
                    new.entry <- data.frame(
                        entry$RANK
                      , paste0(LINK.PRE, release.url, LINK.MID,
                               release.trunc, LINK.END)
                      , artist
                      , release
                      , entry$GENRE
                      , entry$POWER.INDEX
                      , TREND.NEW
                      , stringsAsFactors = FALSE
                    )
                    if (!trend) new.entry <- new.entry[ , -7]
                    return(setNames(new.entry, names(entry)))
                }
            }
        }
    }
    ## try next artist in list
    return(findEntry(artists, entry, firstAttempt, topTrackOnly, artistIter = artistIter + 1))
}

BASE_URL <- "https://api.spotify.com"
API_VERSION <- 'v1'
SEARCH_URL <- glue::glue('{BASE_URL}/{API_VERSION}/search')
ALBUMS_URL <- glue::glue('{BASE_URL}/{API_VERSION}/albums')
ARTISTS_URL <- glue::glue('{BASE_URL}/{API_VERSION}/artists')
## authorize spotifyr
config <- read.csv("../config/config.csv", stringsAsFactors = FALSE, header = FALSE)
SPOTIFY_CLIENT_ID = config[config[[1]] == "SPOTIFY_CLIENT_ID", 2]
SPOTIFY_CLIENT_SECRET = config[config[[1]] == "SPOTIFY_CLIENT_SECRET", 2]
spotifyr::set_credentials(
    client_id = SPOTIFY_CLIENT_ID
  , client_secret = SPOTIFY_CLIENT_SECRET
)
SPOTIFY_ACCESS_TOKEN <- spotifyr::get_tokens()$access_token
assign('access_token', SPOTIFY_ACCESS_TOKEN, envir = .GlobalEnv)

unlink("./imgs", recursive = TRUE, force = TRUE)
d.out <- data.frame(
    do.call(rbind, lapply(1:nrow(d.sorted), parseRankings, d.sorted))
  , stringsAsFactors = FALSE
)

## export to CSV
names(d.out)[which(names(d.out) == "X")] <- ""
names(d.out)[which(names(d.out) == "POWER.INDEX")] <- "POWER INDEX"
write.csv(format(d.out), file = file.path("output", out.name), row.names = FALSE)
