/* Photography for the prototypes. Every image is a free photo under the Unsplash License
   (https://unsplash.com/license), checked on its Unsplash page on 4 Nov 2026. Hotlinked from Unsplash's CDN. */
window.EP_PHOTOS = {
  hero:     {id: '1699588999949-e25959a59550', by: 'Haydn',                page: 'https://unsplash.com/photos/ZT3i-6XW8J8', alt: 'Aerial view of a loaded container ship crossing open water'},
  heroAlt:  {id: '1585713181935-d5f622cc2415', by: 'Venti Views',          page: 'https://unsplash.com/photos/FPKnAO-CF6M', alt: 'Aerial view of a container ship cutting through deep blue water'},
  sea:      {id: '1724597500306-a4cbb7d1324e', by: 'Bent Van Aeken',       page: 'https://unsplash.com/photos/0A7YwYhZhWw', alt: 'Top-down view of a loaded container ship on open ocean'},
  yard:     {id: '1494412519320-aa613dfb7738', by: 'CHUTTERSNAP',          page: 'https://unsplash.com/photos/9cCeS9Sg6nU', alt: 'Aerial view of a container yard'},
  port:     {id: '1494412685616-a5d310fbb07d', by: 'CHUTTERSNAP',          page: 'https://unsplash.com/photos/kyCNGGKCvyw', alt: 'Stacked containers in an industrial port from above'},
  night:    {id: '1792751096611-617c45095d7f', by: 'Sondre Millstein',     page: 'https://unsplash.com/photos/cdm1L4MzCWQ', alt: 'Container terminal cranes lit at night'},
  brass:    {id: '1783309239594-f3296901a813', by: 'Thilina Alagiyawanna', page: 'https://unsplash.com/photos/JW6LKDYboeg', alt: 'Ornate brass wind chimes with elephant designs'},
  spices:   {id: '1784501025488-001592b6ee31', by: 'Jameson Berrios',      page: 'https://unsplash.com/photos/tfbzEN-GjW4', alt: 'Colourful spices piled high in a market'},
  cardamom: {id: '1758657996330-095d08451cd9', by: 'Neil P-A',             page: 'https://unsplash.com/photos/dZIs-KaRdu8', alt: 'Dried cardamom pods on a dark surface'},
  loom:     {id: '1640292343595-889db1c8262e', by: 'Akhil Pawar',          page: 'https://unsplash.com/photos/XCd_6nOdzjo', alt: 'A weaver at a handloom in Pochampalle, India'},
  threads:  {id: '1773847099342-33b0381cbe0d', by: 'Esha Verma',           page: 'https://unsplash.com/photos/LeYd0uXln3I', alt: 'Golden threads on a loom in Gwalior, India'},
  leather:  {id: '1598532163257-ae3c6b2524b6', by: 'Irene Kredenets',      page: 'https://unsplash.com/photos/tcVH_BwHtrc', alt: 'Brown woven leather handbag'}
};
window.photoUrl = (key, w = 1600, q = 78) => `https://images.unsplash.com/photo-${EP_PHOTOS[key].id}?auto=format&fit=crop&w=${w}&q=${q}`;
window.SECTOR_META = {
  handicrafts: {label: 'Handicrafts & brassware',        short: 'Handicrafts', photo: 'brass',   detail: 'brass',    hub: 'Moradabad'},
  agro_marine: {label: 'Spices, cashews & marine',       short: 'Agro & marine', photo: 'spices', detail: 'cardamom', hub: 'Kochi'},
  textiles:    {label: 'Home textiles',                  short: 'Textiles',    photo: 'loom',    detail: 'threads',  hub: 'Panipat'},
  leather:     {label: 'Leather goods',                  short: 'Leather',     photo: 'leather', detail: 'leather',  hub: 'Kolkata'}
};
