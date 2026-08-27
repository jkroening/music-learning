library(httr)
library(jsonlite)
library(tibble)
library(dplyr)

new_spotify_token <- function(access_token, refresh_token, client_id, client_secret) {
    token_env <- new.env(parent = emptyenv())
    token_env$access_token  <- access_token
    token_env$refresh_token <- refresh_token
    token_env$client_id     <- client_id
    token_env$client_secret <- client_secret
    class(token_env) <- 'spotify_token'
    return(token_env)
}
 
print.spotify_token <- function(x, ...) {
    cat('<spotify_token> access_token: ', substr(x$access_token, 1, 8),
        '... (auto-refreshes on expiry)\n', sep = '')
    invisible(x)
}
 
.spotify_bearer <- function(authorization) {
    if (inherits(authorization, 'spotify_token')) {
        return(authorization$access_token)
    } else {
        return(authorization)
    }
}
 
.refresh_spotify_token <- function(token_env) {
    res <- httr::RETRY(
        'POST', 'https://accounts.spotify.com/api/token',
        httr::authenticate(token_env$client_id, token_env$client_secret),
        body = list(grant_type = 'refresh_token',
        refresh_token = token_env$refresh_token),
        encode = 'form'
    )
    httr::stop_for_status(res)
    new_token <- jsonlite::fromJSON(
        httr::content(res, as = 'text', encoding = 'UTF-8')
    )
    token_env$access_token <- new_token$access_token
    if (!is.null(new_token$refresh_token)) {
        token_env$refresh_token <- new_token$refresh_token
    }
    invisible(token_env)
}
 
.validate_market <- function(market) {
    if (!is.null(market) && !grepl('^[[:alpha:]]{2}$', market)) {
        stop('"market" must be an ISO 3166-1 alpha-2 country code')
    }
}
 
.spotify_request <- function(method, url, query = list(), authorization,
                              body = NULL, encode = 'json') {
 
    send <- function(token) {
        args <- list(method, url, query = query,
                     httr::add_headers(Authorization = paste('Bearer', token)),
                     encode = encode, terminate_on = c(401, 403, 404))
        if (!is.null(body)) args$body <- body
        do.call(httr::RETRY, args)
    }
    
    res <- send(.spotify_bearer(authorization))
    
    if (httr::status_code(res) == 401 &&
        inherits(authorization, 'spotify_token')) {
        message(
            'Spotify access token expired -- refreshing and retrying...'
        )
        .refresh_spotify_token(authorization)
        res <- send(authorization$access_token)
    }
    
    httr::stop_for_status(res)
    return(res)
}
 
.spotify_get <- function(url, query = list(), authorization) {
    res <- .spotify_request(
        'GET', url, query = query, authorization = authorization
    )
    return(jsonlite::fromJSON(
        httr::content(res, as = 'text', encoding = 'UTF-8'), flatten = TRUE
    ))
}

search_spotify <- function(
    q, type = c('album', 'artist', 'playlist', 'track', 'show', 'episode'),
    market = NULL, limit = 20, offset = 0, include_external = NULL,
    authorization = get_spotify_access_token(), include_meta_info = FALSE
) {

    assertthat::assert_that(
        is.character(q),
        msg = "The parameter 'q' must be a character string."
    )
    if (!is.null(market)) .validate_market(market)
    assertthat::assert_that(
        (limit >= 1 & limit <= 50) & is.numeric(limit) & limit %% 1 == 0,
        msg = "The parameter 'limit' must be an integer between 1 and 50"
    )
    assertthat::assert_that(
        (offset >= 0 & offset <= 10000) & 
            is.numeric(offset) & 
            offset %% 1 == 0,
        msg = "The parameter 'offset' must be an integer between 1 and 50"
    )
    if (!is.null(include_external)) {
        assertthat::assert_that(
            include_external == 'audio',
            msg = "'include_external' must be 'audio' or an empty string."
        )
    }

    res <- .spotify_get(
        'https://api.spotify.com/v1/search',
        query = list(
            q = q,
            type = paste(type, collapse = ','),
            market = market,
            limit = limit,
            offset = offset,
            include_external = include_external
        ),
        authorization = authorization
    )

    if (!include_meta_info && length(type) == 1) {
        res <- tibble::as_tibble(res[[paste0(type, 's')]]$items)
    }
    return(res)
}

get_track <- function(id,
                      market = NULL,
                      authorization = get_spotify_access_token()) {
    if (!is.null(market)) .validate_market(market)
    return(.spotify_get(
        paste0('https://api.spotify.com/v1/tracks/', id),
        query = list(market = market),
        authorization = authorization
    ))
}

get_tracks <- function(ids,
                       market = NULL,
                       authorization = get_spotify_access_token(),
                       include_meta_info = FALSE) {

    if (!is.null(market)) .validate_market(market)

    track_json <- vapply(ids, function(id) {
        res <- httr::RETRY(
        'GET', paste0('https://api.spotify.com/v1/tracks/', id),
        query = list(market = market),
        httr::add_headers(Authorization = paste('Bearer', authorization)),
        encode = 'json'
        )
        httr::stop_for_status(res)
        httr::content(res, as = 'text', encoding = 'UTF-8')
    }, character(1), USE.NAMES = FALSE)

    combined <- paste0('{"tracks":[', paste(track_json, collapse = ','), ']}')
    res <- jsonlite::fromJSON(combined, flatten = TRUE)

    if (!include_meta_info) {
        res <- res$tracks
    }
    return(res)
}

get_album <- function(id,
                      market = NULL,
                      authorization = get_spotify_access_token()) {
    if (!is.null(market)) .validate_market(market)
    return(.spotify_get(
        paste0('https://api.spotify.com/v1/albums/', id),
        query = list(market = market),
        authorization = authorization
    ))
}

get_album_tracks <- function(id,
                             limit = 20,
                             offset = 0,
                             market = NULL,
                             authorization = get_spotify_access_token(),
                             include_meta_info = FALSE) {

    if (!is.null(market)) .validate_market(market)

    res <- .spotify_get(
        paste0('https://api.spotify.com/v1/albums/', id, '/tracks'),
        query = list(market = market, offset = offset, limit = limit),
        authorization = authorization
    )
    if (!include_meta_info) res <- res$items
    return(res)
}

get_artist_albums <- function(id,
                              include_groups = c(
                                'album', 'single', 'appears_on', 'compilation'
                              ),
                              market = NULL,
                              limit = 20,
                              offset = 0,
                              authorization = get_spotify_access_token(),
                              include_meta_info = FALSE) {

    if (!is.null(market)) .validate_market(market)

    res <- .spotify_get(
        paste0('https://api.spotify.com/v1/artists/', id, '/albums'),
        query = list(include_groups = paste(include_groups, collapse = ','),
                    market = market, limit = limit, offset = offset),
        authorization = authorization
    )
    if (!include_meta_info) res <- res$items
    return(res)
}

get_artist_top_tracks <- function(id,
                                  market = 'US',
                                  authorization = get_spotify_access_token(),
                                  include_meta_info = FALSE) {

    if (!is.null(market)) .validate_market(market)

    res <- .spotify_get(
        paste0('https://api.spotify.com/v1/artists/', id, '/top-tracks'),
        query = list(market = market),
        authorization = authorization
    )
    if (!include_meta_info) res <- res$tracks
    return(res)
}

follow_artists_or_users <- function(
    type, ids = NULL, authorization = get_spotify_authorization_code()
) {

    type <- match.arg(type, choices = c('artist', 'user'))
    if (is.null(ids)) stop('"ids" is required.')

    uris <- paste0('spotify:', type, ':', ids)

    res <- httr::RETRY(
        'PUT', 'https://api.spotify.com/v1/me/library',
        httr::add_headers(Authorization = paste('Bearer', authorization)),
        query = list(uris = paste(uris, collapse = ',')),
        encode = 'json'
    )
    httr::stop_for_status(res)
    return(res)
}

unfollow_artists_or_users <- function(
    type, ids, authorization = get_spotify_authorization_code()
) {

    type <- match.arg(type, choices = c('artist', 'user'))
    uris <- paste0('spotify:', type, ':', ids)

    res <- httr::RETRY(
        'DELETE', 'https://api.spotify.com/v1/me/library',
        httr::add_headers(Authorization = paste('Bearer', authorization)),
        query = list(uris = paste(uris, collapse = ',')),
        encode = 'json'
    )
    httr::stop_for_status(res)
    return(res)
}