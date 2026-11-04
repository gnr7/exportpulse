/* Photography, served locally from /static/photos (800 / 1600 / 2400 px wide).
   Every image is a free photo under the Unsplash License; the record for each is in PHOTO-LICENSES.md. */
window.EP_PHOTOS = {
  hero:     {by: 'Haydn',                page: 'https://unsplash.com/photos/ZT3i-6XW8J8', alt: 'Aerial view of a loaded container ship crossing open water'},
  sea:      {by: 'Bent Van Aeken',       page: 'https://unsplash.com/photos/0A7YwYhZhWw', alt: 'Top-down view of a loaded container ship on open ocean'},
  yard:     {by: 'CHUTTERSNAP',          page: 'https://unsplash.com/photos/9cCeS9Sg6nU', alt: 'Aerial view of a container yard'},
  port:     {by: 'CHUTTERSNAP',          page: 'https://unsplash.com/photos/kyCNGGKCvyw', alt: 'Stacked containers in an industrial port from above'},
  night:    {by: 'Sondre Millstein',     page: 'https://unsplash.com/photos/cdm1L4MzCWQ', alt: 'Container terminal cranes lit at night'},
  brass:    {by: 'Thilina Alagiyawanna', page: 'https://unsplash.com/photos/JW6LKDYboeg', alt: 'Ornate brass wind chimes with elephant designs'},
  spices:   {by: 'Jameson Berrios',      page: 'https://unsplash.com/photos/tfbzEN-GjW4', alt: 'Colourful spices piled high in a market'},
  cardamom: {by: 'Neil P-A',             page: 'https://unsplash.com/photos/dZIs-KaRdu8', alt: 'Dried cardamom pods on a dark surface'},
  loom:     {by: 'Akhil Pawar',          page: 'https://unsplash.com/photos/XCd_6nOdzjo', alt: 'A weaver at a handloom in Pochampalle, India'},
  threads:  {by: 'Esha Verma',           page: 'https://unsplash.com/photos/LeYd0uXln3I', alt: 'Golden threads on a loom in Gwalior, India'},
  leather:  {by: 'Irene Kredenets',      page: 'https://unsplash.com/photos/tcVH_BwHtrc', alt: 'Brown woven leather handbag'}
};
/* smallest stored width that covers the request */
window.photoUrl = (key, w = 1600) => `/static/photos/${key}-${w <= 800 ? 800 : w <= 1600 ? 1600 : 2400}.jpg`;
window.SECTOR_META = {
  handicrafts: {label: 'Handicrafts & brassware',  short: 'Handicrafts',   photo: 'brass',   detail: 'brass',    hub: 'Moradabad'},
  agro_marine: {label: 'Spices, cashews & marine', short: 'Agro & marine', photo: 'spices',  detail: 'cardamom', hub: 'Kochi'},
  textiles:    {label: 'Home textiles',            short: 'Textiles',      photo: 'loom',    detail: 'threads',  hub: 'Panipat'},
  leather:     {label: 'Leather goods',            short: 'Leather',       photo: 'leather', detail: 'leather',  hub: 'Kolkata'}
};
