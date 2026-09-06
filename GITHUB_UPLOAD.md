================================================================================
                   HOW TO UPLOAD PARAKH OCR TO GITHUB
================================================================================

OPTION A: If you HAVE a GitHub account (Recommended)
─────────────────────────────────────────────────────

STEP 1: Create a New Repository on GitHub.com
──────────────────────────────────────────────
1. Go to https://github.com/new
2. Login with your GitHub account (if not already logged in)
3. Fill in:
   - Repository name: parakh-ocr-ui (or whatever you want)
   - Description: "OCR extraction for Indian food package labels"
   - Choose: Public (so anyone can see/use it) or Private (only you)
   - ✓ Add a README.md (auto-generates one)
   - ✓ Add .gitignore (select Python)
   - License: MIT (recommended for open-source)
4. Click "Create repository"

You'll see a page with commands. Copy the HTTPS URL (looks like):
   https://github.com/your-username/parakh-ocr-ui.git


STEP 2: Navigate to Your Project Directory
────────────────────────────────────────────
Open terminal/command prompt and go to your parakh-ocr-ui folder:

$ cd /path/to/parakh-ocr-ui

Confirm you're in the right place:
$ ls
# Should show: app.py, index.html, requirements.txt, extraction_lib/, etc.


STEP 3: Initialize Git (First Time Only)
─────────────────────────────────────────
$ git init
$ git add .
$ git commit -m "Initial commit: PARAKH OCR with UI"

(This creates git history locally on your computer)


STEP 4: Add Your GitHub Remote and Push
────────────────────────────────────────
Replace YOUR-USERNAME and YOUR-REPO-NAME with actual values:

$ git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
$ git branch -M main
$ git push -u origin main

On first push, you'll be prompted for credentials:
  Username: your-github-username
  Password: (paste a Personal Access Token — see Step 4b below)


STEP 4B: GitHub Personal Access Token (If Password Fails)
──────────────────────────────────────────────────────────
Modern GitHub requires a token, not password. Get one:

1. Go to https://github.com/settings/tokens/new
2. Click "Generate new token (classic)"
3. Give it a name: "parakh-ocr-upload"
4. Check these scopes:
   ✓ repo (all)
   ✓ workflow
5. Click "Generate token"
6. Copy the token immediately (you won't see it again)
7. Use the token as your "password" when git asks

Or set it up permanently so git remembers:
$ git config --global credential.helper store
$ git push  # First time, enter token. After that, it's automatic.


STEP 5: Verify It Worked
────────────────────────
Check your GitHub repo online:
  https://github.com/YOUR-USERNAME/YOUR-REPO-NAME

You should see all your files there:
  ✓ app.py
  ✓ index.html
  ✓ requirements.txt
  ✓ extraction_lib/
  ✓ SETUP.md
  ✓ README.md (auto-generated)


================================================================================
OPTION B: If you DON'T Have a GitHub Account Yet
──────────────────────────────────────────────────

STEP 1: Create GitHub Account
──────────────────────────────
1. Go to https://github.com/join
2. Sign up with email, create username and password
3. Verify email address
4. Choose Free plan (click "Continue")
5. Done! Now follow Option A steps above.


================================================================================
AFTER UPLOAD: Making Changes & Syncing
──────────────────────────────────────

If you edit files locally and want to update GitHub:

$ git add .                          # Stage all changes
$ git commit -m "Describe what changed"
$ git push                           # Upload to GitHub

Example workflow after testing the UI:
$ git add .
$ git commit -m "Fix batch number regex for 'lot no' false positives"
$ git push

Now your GitHub repo is updated.


================================================================================
CLONE YOUR REPO ON ANOTHER COMPUTER
────────────────────────────────────

If you want to download this project on another computer (or phone via Gitpod):

$ git clone https://github.com/YOUR-USERNAME/parakh-ocr-ui.git
$ cd parakh-ocr-ui
$ pip install -r requirements.txt
$ python app.py


================================================================================
USEFUL .gitignore ADDITIONS
───────────────────────────

GitHub auto-generated .gitignore for Python. Add these lines to ignore 
large/temporary files:

# OCR model files (downloaded on first run, don't commit)
*.pdmodel
*.pdiparams
*.pdiparams.info

# Uploaded images (temp files)
*.jpg
*.jpeg
*.png
*.gif
*.webp

# Virtual environments
venv/
env/

# IDE
.vscode/
.idea/

Add these to your .gitignore file and commit:
$ echo "*.jpg\n*.jpeg\n*.png" >> .gitignore
$ git add .gitignore
$ git commit -m "Update gitignore to exclude images and model files"
$ git push


================================================================================
TROUBLESHOOTING
═══════════════

❌ "fatal: not a git repository"
   → You didn't run `git init` in step 3. Do that first.

❌ "Permission denied (publickey)"
   → SSH key issue. Use HTTPS instead of SSH.
     Check: $ git remote -v
     Should show: https://github.com/...
     If it shows git@github.com:... change it:
     $ git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO.git

❌ "authentication failed"
   → Wrong token or password. Generate a Personal Access Token (Step 4B).

❌ "rejected... main vs master"
   → Old git default. This was fixed in Step 4 (git branch -M main).

❌ "Please commit your changes or stash them before you merge"
   → You have uncommitted changes. Do:
     $ git add .
     $ git commit -m "Your message"
     $ git push


================================================================================
OPTIONAL: Use GitHub Desktop (GUI Instead of Terminal)
───────────────────────────────────────────────────────

If you hate terminal, use GitHub Desktop:
1. Download: https://desktop.github.com
2. Sign in with GitHub account
3. File → Clone Repository → paste GitHub URL
4. Select local folder
5. Make changes locally, "Commit to main", "Push to origin"
6. All same result, just GUI


================================================================================
OPTIONAL: Deploy to Render or Vercel (Run Your App Online)
───────────────────────────────────────────────────────────

Once on GitHub, you can host it free:

For Backend (Flask):
  → Render.com (free tier, auto-deploys from GitHub)
  → Railway.app
  → PythonAnywhere.com

For Frontend (React):
  → Vercel.com (auto-deploys from GitHub)
  → Netlify.com

Many of these support one-click "Connect GitHub repo" → auto-deploy.
See SETUP.md for more details.


================================================================================
THAT'S IT!
──────────

Questions? Check GitHub Docs: https://docs.github.com
