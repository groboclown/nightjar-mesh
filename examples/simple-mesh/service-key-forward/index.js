const express = require("express");
const axios = require("axios");

const PORT = process.env.PORT || 3000;
const app = express();

(process.env.KEYS || '').split(',').forEach(key => {
  if (key && key.trim().length > 0) {
    key = key.trim();
    let env_key = key.toUpperCase() + '_VALUE';
    let value = process.env[env_key] || key;
    app.get(`/key/${key}`, (req, res) => {
      res.type('json');
      res.send(`{"value":"${value}"}`);
    });
    console.log(` - Listening for /key/${key} -> ${value}`);
  }
});

(process.env.FORWARD_KEYS || '').split(',').forEach(key => {
  if (key && key.trim().length > 0) {
    key = key.trim();
    let env_key = key.toUpperCase() + "_URL";
    let url = process.env[env_key];
    if (url && url.length > 0) {
      app.get(`/forward/${key}`, (req, res) => {
        axios
          .get(url)
          .then(response => {
            res.status(response.status);
            res.send(response.data);
          })
          .catch(error => {
            console.log(error);
            res.status(406);
            res.send('Forwarded response returned an error.');
          });
      });
      console.log(` - Forwarding /forward/${key} to ${url}`)
    }
  }
});

app.listen(PORT, () => {
  console.log(`Server is listening on port: ${PORT}`);
});
