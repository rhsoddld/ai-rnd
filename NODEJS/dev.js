const express = require('express')
const router = express.Router()

const { exec } = require('child_process');

router.get("/", (req, res) => {
    res.send("/ssh endpoint is active.");
});

router.post("/", (req, res) => {
    const sshCommand = req.body.ssh;
    console.log(sshCommand)
    // res.send("Perfect");

    exec(sshCommand, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            return res.status(500).json({
                message: 'Command execution failed',
                error: error.message
            });
        }

        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);

        res.status(201).json({
            message: 'Command executed successfully',
            stdout: stdout,
            stderr: stderr
        });
    });
});

module.exports = router; 

