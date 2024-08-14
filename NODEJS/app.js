const express = require("express");
const app = express()
const port = 3000

app.use(express.json());

const devRouter = require("./route/dev.js")

app.use("/dev", devRouter)

app.get('/', (req, res) => {
  res.send('Hello World!')
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})