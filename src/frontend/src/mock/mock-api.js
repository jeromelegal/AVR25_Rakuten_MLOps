const express = require('express');
const fs = require('fs');
const app = express();
app.use(express.json({ limit: '10mb' }));

app.post('/api/internal/mongodb/entity/ad', (req, res) => {
  const ads = fs.existsSync('tmp_ads.json')
    ? JSON.parse(fs.readFileSync('tmp_ads.json'))
    : [];
  ads.push(req.body);
  fs.writeFileSync('tmp_ads.json', JSON.stringify(ads, null, 2));
  res.json({ message: 'Mock ad saved!', ad: req.body });
});

app.listen(4000, () => console.log('Mock API running on port 4000'));