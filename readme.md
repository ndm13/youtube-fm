# youtube-fm
A bridge between YouTube Music and Last.FM.

I have found [exactly one](https://ytmusicapi.readthedocs.io/en/latest/index.html)
YouTube Music API.  It is written in Python and is relatively limited, and that
reflects on this project as well.  Additionally, there are two maintained Python
Last.FM APIs: [`pylast`](https://github.com/pylast/pylast), which relies on an
MD5-hashed user password, and [`lastpy`](https://github.com/huberf/lastfm-scrobbler),
which is a bit clunky and doesn't support custom timestamps
([yet](https://github.com/huberf/lastfm-scrobbler/pull/3)).  Currently we're rolling
our own Last.FM integration based on `lastpy`.

## Limitations
This project works around limitations from YouTube Music in a few ways:
1. **The API does not include a subscription for playback events.**  We pull the
   playback history and backtrack to the last played track, then submit scrobbles for
   each of those tracks.
2. **The History list (on Google's side) does not allow duplicates.**  This means we
   cannot count how many times a song was looped, and causes more problems since...
3. **The API does not include playback timestammps.**  When pulling the history, we
   rely on the last playback ID found as a bookmark.  This is unreliable and has many
   edge cases:
   - We can't tell if a track has been played in a loop with other tracks.  A playlist
     with songs A, B, and C will only show those three tracks no matter how many times
     it's looped.
   - Rolling back to the last played track is Hard™.  We store the track ID (YouTube
     video slug) of the last track we found and cut the history there.  So if you
     played 500 tracks between now and the last run, if you ended with the same one
     you ended with last time, we'll find zero.
   - Timestamps are impossible and complete guesswork.  Currently we grab the current
     timestamp when running the pull and assume you started the current track at that
     time, then backtrack that through all tracks in history by length.  So if the
     track you played before this one is three minutes long, we'll assume you played
     it three minutes ago.  It's absolutely imperfect and makes tons of assumptions,
     but it's better than submitting them as all played simultaneously.
   - Playback duration is impossible to track.  Most Last.FM scrobblers let you define
     a minimum playback duration, but since we cannot track start/stop times we will
     always assume it was played in full.  Again, very imperfect, but not much we can
     do about it without more API info.

## Setup and Use
With these limitations in mind, the intended use is a bit interesting: *run the script
frequently.*  Good idea to have a sane limit (haven't load tested anything yet) of
maybe 5-10 minutes, but probably not longer than once an hour.  Unless you're skipping
through vast amounts of unique songs, you're unlikely to hit the Last.FM API limit,
but considering that the YouTube Music API relies on browser cookies it's probably a
good idea not to overdrive that, lest your actual YouTube account get flagged.

Speaking of cookies, let's set this up:
1. Clone the project:
   ```bash
   $ git clone https://github.com/ndm13/youtube-fm.git
   ```
2. Get the browser cookies for the YouTube Music API (see: [Authenticated Requests on ytmusicapi Docs](https://ytmusicapi.readthedocs.io/en/latest/setup.html#authenticated-requests)).
   The setup scripts from this library are integrated: if you don't have a
   `headers_auth.json` file, the script will walk you through generating one.  I
   personally had issues with reading this from stdin, so there's the option of adding
   the headers to a file (path stored in `HEADERS_FILE` environment variable, `.env`
   supported) that will be used for setup instead.
   ```bash
   $ python main.py
   Please paste the request headers from Firefox and press 'Enter, Ctrl-Z, Enter' to continue:
   ```
3. Setup a Last.FM API key and secret (see: [Last.FM API Docs](http://www.last.fm/api/authentication)).
   Store these in `LASTFM_API` and `LASTFM_SECRET` environment variables (`.env`
   supported).
4. Generate a user token.  This will let you perform your first pull and set you up
   with a session token that you can use for all future runs.  Running the script
   without either `LASTFM_TOKEN` or `LASTFM_SESSION` set will give you the link you
   need to use to generate a token. *Note: if you use port 5555 for anything, please
   change the port number in the link to an unused port.*
   ```bash
   $ python main.py
   ERROR:root:You will need to generate a user token:
   ERROR:root:https://www.last.fm/api/auth?api_key=<your_api_token>=http://localhost:5555
   Traceback (most recent call last):
     File "main.py", line 53, in <module>
       raise Exception("Can't authenticate! Set LASTFM_TOKEN or LASTFM_SESSION to access Last.FM")
   Exception: Can't authenticate! Set LASTFM_TOKEN or LASTFM_SESSION to access Last.FM
   ```
   Clicking the Authorize button on that page will redirect you to a nonexistent
   localhost page with a url like `http://localhost:5555/?token=<some_token_here>`.
   Copy everything after the equals sign and store it in the `LASTFM_TOKEN` environment
   variable (`.env` supported).
5. On first run, the history will be pulled and scrobbled, but you will get a warning
   about setting the `LASTFM_SESSION` environment variable:
   ```bash
   $ python main.py
   WARNING:root:Using LASTFM_TOKEN: You will need to generate a new token every run!
   WARNING:root:To prevent this, set the LASTFM_SESSION environment variable generated below:
   WARNING:root:	LASTFM_SESSION=<some_session_id>
   INFO:root:Scrobbling 'and the day goes on' by bill wurtz
   INFO:root:Scrobbling 'Lemon Demon - Everybody Likes You' by Neil Cicierega
   INFO:root:Scrobbling 'The Business of Emotion (feat. White Sea)' by Big Data
   INFO:root:Writing ID NHZr6P1csiY as new last
   ```
   Set the `LASTFM_SESSION` variable as shown (`.env` supported).
6. Did you notice this line?
   ```
   INFO:root:Scrobbling 'Lemon Demon - Everybody Likes You' by Neil Cicierega
   ```
   That's a lie: the title includes the artist.  YouTube isn't smart enough to figure
   this out, but we can try to hack around it by saying `artist - title` means the
   artist is `artist` and the title is `title`.  You can enable this by setting the
   environment variable `SPLIT_TITLE` to `true` (again, `.env` supported).  Don't do
   this if you have lots of music that does use dashes and doesn't use this naming
   convention.
7. The default log level is `INFO`.  You can change it by setting the environment
   variable `LOG_LEVEL` per the Python logging spec.

## Future Improvements
This is the minimum product I'm comfortable releasing after a long night of relearning
Python.  There are some definite quality of life improvements to be made:
- [ ] **HTTP server:**

  We should be able to receive that callback and store the token ourselves, preferably
  in...
- [ ] **A database:**

  Tracking users, tokens, cookies, etc.  Foundations of a multi-user system with Last.FM
  federation.
- [ ] **Docker container:**

  Because Docker makes everything better.  Preferably not just the `main.py`, but a `cron`
  job or some other automation to run at *n* interval.
- [ ] **Wait for YouTube Music API to get better:**

  Either the unofficial version or (hopefully) an official version with the necessary
  features.
- [ ] **An automation to capture cookies:**

  This is the highest bar for casual adoption. Not sure how to solve this, but I know
  there are already extensions that do this for YouTube-DL-type services.  Needs
  investigation, may be able to repurpose an existing extension.
- [ ] **Python is not my language of choice:**

  If you see something wrong from a style or convention perspective let me know!  I'd love
  to get this ported to Deno or something like that, but I want to keep support for the
  *only* existing YouTube Music API for now so it's going to stay Python for the time
  being.
