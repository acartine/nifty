import React, { useState } from 'react';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import './ShortenForm.css';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

interface ShortenFormProps { }

interface Payload {
  short_url: string
}

const ShortenForm: React.FC<ShortenFormProps> = () => {
  // Use state to store the long URL and short URL
  const [longUrl, setLongUrl] = useState('');
  const [payload, setPayload] = useState<Payload | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCloseSnackbar = (_event: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }

    setCopied(false);
  };

  // Define a function to handle form submission
  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    // Send a POST request to the /shorten endpoint to create a new short URL
    fetch('/shorten', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ long_url: longUrl }),
    })
      .then((response) => response.json())
      .then((payload: Payload) => {
        // Update the state with the new short URL
        setPayload(payload);
      });
  };

  //hack for local dev
  let host;
  if (payload) {
    host = window.location.host;
    if (host.endsWith('3000')) {
      host = host.replace('3000', '5000')
    }
  }
  const urlLink = payload ? window.location.protocol + '//' + host + '/' + payload.short_url : null;

  const copyToClipboard = () => {
    if (urlLink) {
      navigator.clipboard.writeText(urlLink)
      setCopied(true)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <Grid container spacing={2} paddingTop={2} alignItems='center'>
          <Grid item xs={10}>
            <TextField
              label="Long URL"
              value={longUrl}
              fullWidth
              onChange={(event) => setLongUrl(event.target.value)}
            />
          </Grid>
          <Grid item xs={2} sx={{ alignItems: 'center' }}>
            <Button type="submit" variant="contained" color="primary">
              Shorten
            </Button>
          </Grid>
          {urlLink &&
            <Grid item xs={12}>
              <Box sx={{ alignItems: 'center', paddingLeft: 2, display: 'inline-flex' }}>
                <Link href={urlLink} target="_blank" underline={'hover'} rel={'noreferrer'}>
                  <Typography>
                    {urlLink}
                  </Typography>
                </Link>
                <Button sx={{ marginLeft: 2 }} onClick={copyToClipboard} variant="contained" color="primary">
                  Copy
                </Button>
              </Box>
            </Grid>
          }
        </Grid>
      </form>
      <Snackbar
        open={copied}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success">
          {urlLink} copied to clipboard.
        </Alert>
      </Snackbar>
    </div>
  );
};

export default ShortenForm
