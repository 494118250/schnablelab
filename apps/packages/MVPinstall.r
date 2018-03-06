pkg <- c(
	"Rcpp_0.12.12.tar.gz",
	"RcppEigen_0.3.2.9.0.tar.gz",
	"bigmemory.sri_0.1.3.tar.gz",
	"BH_1.62.0-1.tar.gz",
	"bigmemory_4.5.19.tar.gz",
	"codetools_0.2-15.tar",
	"iterators_1.0.8.tar",
	"foreach_1.4.3.tar",
	"DBI_0.7.tar",
	"biglm_0.9-1.tar",
	"biganalytics_1.1.14.tar.gz",
	"BiocGenerics_0.22.0.tar.gz",
	"zlibbioc_1.22.0.tar.gz",
	"snpStats_1.26.0.tar.gz",
	"irlba_2.2.1.tar.gz",
	"proftools_0.99-2.tar",
	"NCmisc_1.1.5.tar",
	"reader_1.0.6.tar",
	"bigpca_1.0.3.tar.gz",
	"rfunctions_0.1.tar.gz",
	"MVP_1.0.1.tar.gz"
)
pkg.install <- do.call(rbind, strsplit(pkg, "_"))[, 1]
pkg.installed <- installed.packages()[,c("Package")]
pkg.index <- !pkg.install %in% pkg.installed
pkg.index[length(pkg.index)] <- TRUE
if(!pkg.index[2] && (packageVersion("RcppEigen") > package_version("0.3.2.9.0")))	pkg.index[2] <- TRUE
pkg <- pkg[pkg.index]
for(p in 1:length(pkg)){install.packages(pkg[p], repos=NULL)}
logi <- sum(pkg.install %in% installed.packages()[,c("Package")])==length(pkg.install)
cat("\n")
if(logi)	cat("MVP installation accomplished successfully!\n")
cat("\n")
