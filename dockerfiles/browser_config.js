export default {
  catalogUrl: "http://0.0.0.0:8081",
  catalogTitle: "eoAPI STAC Browser",
  catalogTitleAfterImage: null,
  catalogImage: null,
  allowExternalAccess: true, // Must be true if catalogUrl is not given
  allowedDomains: [],
  enforcedColorMode: "auto",
  detectLocaleFromBrowser: true,
  storeLocale: true,
  locale: "en",
  fallbackLocale: "en",
  supportedLocales: [
    "ar",
    "de",
    "es",
    "en",
    "fr",
    "it",
    "ro",
    "ru",
    "ja",
    "pt",
    "id",
    "pl",
    "sv",
  ],
  apiCatalogPriority: null,
  useTileLayerAsFallback: true,
  displayGeoTiffByDefault: false,
  displayPreview: true,
  displayOverview: true,
  displayOverviewsForChildren: false,
  buildTileUrlTemplate: (asset) => {
    const href = asset.getAbsoluteUrl();
    const assetHref = asset.href || href;
    const tileHref = assetHref.startsWith("/vsi") ? assetHref : href;

    return (
      "http://0.0.0.0:8082/external/tiles/WebMercatorQuad/{z}/{x}/{y}?url=" +
      encodeURIComponent(tileHref)
    );
  },
  getMapSourceOptions: null,
  pathPrefix: "/",
  historyMode: "history",
  cardViewMode: "cards",
  defaultCollectionSort: "title",
  defaultItemSort: null,
  showKeywordsInItemCards: false,
  showKeywordsInCatalogCards: false,
  preferredAssets: true,
  showThumbnailsAsAssets: false,
  searchResultsPerPage: null,
  itemsPerPage: 12,
  collectionsPerPage: null,
  maxEntriesPerPage: 1000,
  defaultThumbnailSize: null,
  crossOriginMedia: null,
  requestHeaders: {},
  requestQueryParameters: {},
  socialSharing: ["email", "bsky", "mastodon", "x"],
  preprocessSTAC: null,
  authConfig: null,
  crs: {},
  footerLinks: null,
};
