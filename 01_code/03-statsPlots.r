## If a package is installed, it will be loaded. If any 
## are not, the missing package(s) will be installed 
## from CRAN and then loaded.

setwd("C:/Users/andrei.c/Desktop/2020_examinari/")

## First specify the packages of interest
packages = c("data.table", "jsonlite", "ggplot2", "ggpubr", 
             "fuzzyjoin", "dplyr", "stringi", "stringr")

## Now load or install&load all
package.check <- lapply(
  packages,
  FUN = function(x) {
    if (!require(x, character.only = TRUE)) {
      install.packages(x, dependencies = TRUE)
      library(x, character.only = TRUE)
    }
  }
)
rm(package.check)

# Load settlements json
settlements_json <- read_json("settlements_all.json", simplifyVector = T, flatten = T)

# Transform settlements json to df
settlements_df <- lapply(settlements_json, function(x) {
  x[sapply(x, is.null)] <- NA
  unlist(x)
})

settlements_df <- data.table(as.data.frame(do.call("cbind", settlements_df)))
rm(settlements_json)

# Remove duplicate names for settlements in df
setkey(settlements_df, nume_judet, nume_localitate)
settlements_df <- settlements_df[!duplicated(settlements_df, by = key(settlements_df))]
settlements_df <- rbindlist(list(settlements_df, 
                                 list("bucuresti", 4217, 2121794, 
                                      2121794/15106, "bucuresti", "municipiu")))

settlements_df$nume_localitate_search <- paste0(settlements_df$nume_localitate, "$")
#settlements_df$nume_localitate <- paste0(".*", settlements_df$nume_localitate)

# Load evaluate nationala json
en_json <- read_json("evaluare_nationala_new.json", simplifyVector = T, flatten = T)

en_df <- lapply(en_json, function(x) {
  x[sapply(x, is.null)] <- NA
  unlist(x)
})

en_df <- data.table(as.data.frame(do.call("cbind", en_df)))
rm(en_json)

# Assign correct settlement type
# Load from Wikipedia and merge
settlements_wiki <- fread("settle_wiki.csv", stringsAsFactors = F)
setkey(settlements_wiki, nume_judet, nume_localitate)
settlements_wiki <- settlements_wiki[!duplicated(settlements_wiki, by = key(settlements_wiki))]
settlements_wiki <- rbindlist(list(settlements_wiki, 
                                 list("bucuresti", "bucuresti", "municipiu")))

setkey(settlements_df, nume_judet, nume_localitate)
setkey(settlements_wiki, nume_judet, nume_localitate)
settlements_df <- settlements_df[settlements_wiki]
settlements_df <- settlements_df[,-"tip_localitate"]
colnames(settlements_df)[7] <- "tip_localitate"
rm(settlements_wiki)

settlements_df$tip_localitate[ settlements_df$nume_localitate == "vardotfalva"] <- "sat"

settlements_df$teritoriu <- ifelse(settlements_df$tip_localitate == "sat", "rural", "urban")

######
county_names <- unique(settlements_df$nume_judet)
county_codes <- c("AB", "AR", "AG", "BC", "BH", "BN", "BT",
                  "BR", "BV", "B", "BZ", "CL", "CS", "CJ", "CT", 
                  "CV", "DB", "DJ", "GL", "GR", "GJ", "HR", 
                  "HD", "IL", "IS", "IF", "MM", "MH", "MS", 
                  "NT", "OT", "PH", "SJ", "SM", "SB", "SV", 
                  "TR", "TM", "TL", "VL", "VS", "VN")
county_keys <- data.table(name=county_names, code=county_codes)

en_df <- merge(en_df, county_keys, by.x = "cod_judet", by.y = "code")
colnames(en_df)[15] <- "nume_judet"

################
################
###############
df_list <- list()
for(county in county_names){
  test <- en_df[ en_df$nume_judet == county] %>%
    regex_inner_join(settlements_df[ settlements_df$nume_judet == county], 
                     by = c(scoala = "nume_localitate_search"))
  test2 <- en_df[! en_df$scoala %in% test$scoala & en_df$nume_judet == county]
  
  combined <- rbindlist(list(test, test2), use.names = T, fill = T)
  
  df_list <- append(combined, list(listtmp))
}

all_df <- rbindlist(df_list, fill = T)

en_df_no_absent <- en_df[ en_df$media_totala_curenta != "Absent"]
en_df_no_absent$media_totala_curenta <- as.numeric(en_df_no_absent$media_totala_curenta)

en_df_no_absent[,count := .N, by="cod_judet"]
en_df_no_absent <- transform(en_df_no_absent, count = 1 - count/nrow(en_df_no_absent))

gghistogram(en_df_no_absent[ en_df_no_absent$cod_judet != "B"], x = "media_totala_curenta",
            add = "median", facet.by = "cod_judet",
            rug = F,
            ggtheme = theme_bw())


####
en_df_romana <- en_df[en_df$romana_contestatie != "-",]
en_df_mate <- en_df[en_df$matematica_contestatie != "-",]

en_df_romana[,4:6] <- lapply(en_df_romana[,4:6], as.numeric)
en_df_mate[,7:9] <- lapply(en_df_mate[,7:9], as.numeric)

mean(en_df_romana$romana_nota_finala - en_df_romana$romana_nota)

wilcox.test(en_df_romana$romana_nota_finala, 
            en_df_romana$romana_nota, 
            paired = TRUE, 
            alternative = "two.sided")

gghistogram(en_df_romana, x = "romana_nota",
            add = "mean", rug = TRUE,
            y = "romana_nota_finala", merge = T) +
  geom_histogram(aes(y = "Frequency"), position="identity")






