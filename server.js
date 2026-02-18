const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Serve everything from the project root so relative paths work:
// viz/index.html loads ../data/embeddings.json  →  /data/embeddings.json  ✓
app.use(express.static(path.join(__dirname)));

// Root redirect → viz
app.get('/', (req, res) => {
  res.redirect('/viz/');
});

app.listen(PORT, () => {
  console.log(`Cocktail Cartography listening on port ${PORT}`);
});
