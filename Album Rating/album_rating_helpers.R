
score <- function(ratings, pop.sd = 1.3360853142453697) {
    if (all(ratings == 1)) return(1.0)
    mean.album <- mean(ratings)
    print(mean.album)
    sd.album <- sd(ratings)
    if (sd.album == 0) sd.album <- 0.25
    print(sd.album)
    ratings[ratings == 4] <- 4 * 1.20
    ratings[ratings == 2] <- 2 * 1.20
    adj.mean <- mean(ratings[ratings != 3])
    if (is.na(adj.mean)) adj.mean <- 3.00
    print(adj.mean)
    album.length <- length(ratings)
    prop.4or5 <- sum(ratings > 3) / album.length
    print(prop.4or5)
    adj1 <- (adj.mean - 3) * prop.4or5
    print(adj1)
    adj2 <- adj1 + sum(ratings >= 3) * 0.03
    print(adj2)
    score <- mean.album + adj2
    print(score)
    if (prop.4or5 == 0) sd.adj <- sd.album * 0.05
    else sd.adj <- sd.album * prop.4or5 / album.length
    print(sd.adj)
    out <- score - sd.adj
    return(out)
}

scale <- function(score, best = 5.662521, worst = 1.0) {
    scaled <- (score - worst) / (best - worst)
    print(scaled)
    scaled
}

scale2 <- function(score, best = -0.125, worst = -1) {
    scaled <- (score - worst) / (best - worst)
    print(scaled * 100)
    round(scaled * 100, 2)
}

index <- function(score) {
    out <- (-1 * (2.68^(-1.2 * score)) * 1.3 + 1.3983) * 100
    round(out, 2)
}

index2 <- function(score) {
    out <- (-1 * (8^(-1 * score)))
    out
}

go <- function(ratings) index2(scale(score(ratings)))

mn3 <- function(ratings) mean(ratings[ratings != 3])

adj <- function(ratings) {
    ratings[ratings == 4] <- 4 * 1.2
    ratings[ratings == 2] <- 2 * 1.2
    ratings
}

adjmean <- function(ratings) {
    ratings[ratings == 4] <- 4 * 1.2
    ratings[ratings == 2] <- 2 * 1.25
    mean(ratings)
}

adjmeannot3 <- function(ratings) {
    ratings[ratings == 4] <- 4 * 1.2
    ratings[ratings == 2] <- 2 * 1.2
    mean(ratings[ratings != 3])
}

counts <- function(ratings) {
    print(sum(ratings == 3))
    print(sum(ratings != 3))
    print(sum(ratings > 3))
}

bump <- function(ratings) {
    sum(adj(ratings) - 3) / length(ratings)
}

go2 <- function(ratings) scale2(index2(scale(score(ratings))))
