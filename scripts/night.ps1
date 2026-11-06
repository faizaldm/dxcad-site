# Runs the autonomous night session headless, in a loop of fresh sessions,
# until BACKLOG.md has no unchecked items or $maxRuns is reached. Logs it.
# Called by Task Scheduler (see register-tasks.ps1) or by hand:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\night.ps1

$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
# Billing (owner rule, 2026-10-03): a key file for this lane means the API key; no file means the subscription.
$keyFile = Join-Path "$env:USERPROFILE\Desktop\DX-CAD-checks\keys" ((Split-Path -Leaf $repo) + ".key")
New-Item -ItemType Directory -Force -Path (Join-Path $repo "logs") | Out-Null
$billLog = Join-Path $repo "logs\night-$(Get-Date -Format yyyy-MM-dd).log"
if (Test-Path -LiteralPath $keyFile) {
  try {
    $sec = Get-Content -LiteralPath $keyFile | ConvertTo-SecureString -ErrorAction Stop
    $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
    "=== $(Get-Date -Format s) billing: API key from $keyFile ===" | Out-File -LiteralPath $billLog -Append -Encoding utf8
  } catch {
    "=== $(Get-Date -Format s) billing: key file $keyFile could not be read; stopping rather than using the subscription ===" | Out-File -LiteralPath $billLog -Append -Encoding utf8
    exit 1
  }
} else {
  Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
  "=== $(Get-Date -Format s) billing: subscription (no key file at $keyFile) ===" | Out-File -LiteralPath $billLog -Append -Encoding utf8
}
$venv = Join-Path $repo ".venv\Scripts\Activate.ps1"
if (Test-Path -LiteralPath $venv) { . $venv }
New-Item -ItemType Directory -Force -Path (Join-Path $repo "logs") | Out-Null

$stamp   = Get-Date -Format "yyyy-MM-dd"
$log     = Join-Path $repo "logs\night-$stamp.log"
# Read the prompt from main, whatever branch the last run left checked out,
# so a config change on main applies to the very next run. Fall back to disk.
$prompt = (git show main:prompts/night.md 2>$null) -join "`n"
if (-not $prompt) { $prompt = Get-Content -Raw -LiteralPath (Join-Path $repo "prompts\night.md") }
$backlog = Join-Path $repo "BACKLOG.md"
$maxRuns = 6

# Same allowlist as .claude/settings.json. Headless runs have no way to
# prompt you, so anything not listed here is denied, not asked.
$extra = @()
$model = "claude-sonnet-5-5"
if ($model) { $extra += @("--model", $model) }
$extra += @("--effort", "high")

$tools = @(
  "Read", "Edit", "Write", "Glob", "Grep",
  "Bash(python:*)", "Bash(py:*)", "Bash(.venv/Scripts/python:*)",
  "Bash(git add:*)", "Bash(git commit:*)", "Bash(git checkout:*)",
  "Bash(git clean:*)", "Bash(git branch:*)", "Bash(git status:*)",
  "Bash(git diff:*)", "Bash(git log:*)", "Bash(git stash:*)",
  "Bash(git rm:*)", "Bash(git mv:*)",
  "Bash(date:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(mkdir:*)",
  "Bash(cd:*)", "Bash(pwd:*)", "Bash(echo:*)", "Bash(find:*)", "Bash(head:*)",
  "Bash(tail:*)", "Bash(grep:*)", "Bash(wc:*)", "Bash(diff:*)", "Bash(sort:*)",
  "Bash(test:*)", "Bash(true:*)", "Bash(cp:*)", "Bash(mv:*)", "Bash(touch:*)"
) -join ","

function Open-Items {
  $m = Select-String -LiteralPath $backlog -Pattern '^- \[ \]' -AllMatches
  if ($null -eq $m) { return 0 }
  return @($m).Count
}

"=== night started $(Get-Date -Format s) ===" | Out-File -LiteralPath $log -Append -Encoding utf8

# A run that starts with an empty backlog is a refill run (see prompts\night.md):
# it drafts items and stops, and the next run builds them. Stop the loop when a
# refill run leaves the backlog still empty, since nothing more can be drafted.
$pause = Join-Path $repo "PAUSE"
for ($i = 1; $i -le $maxRuns; $i++) {
  if (Test-Path -LiteralPath $pause) {
    "=== PAUSE file present; not starting run $i ===" | Out-File -LiteralPath $log -Append -Encoding utf8
    break
  }
  $open = Open-Items
  $headBefore = (& git rev-parse HEAD 2>$null)
  "=== run $i of $maxRuns started $(Get-Date -Format s), $open items open ===" |
    Out-File -LiteralPath $log -Append -Encoding utf8

  # A server error (overloaded, 5xx) is retried after a pause; it must never
  # look like an empty backlog. A usage limit ends the night.
  $attempt = 0
  do {
    $attempt++
    $out = claude -p $prompt --permission-mode acceptEdits --allowedTools $tools --output-format text @extra 2>&1 | Out-String
    $out | Out-File -LiteralPath $log -Append -Encoding utf8
    # Only a session that did not finish counts: a report that merely mentions
    # an error or a limit must not stop the night.
    $finished = $out -match '(?m)^\s*FINISHED\s*$'
    $limit    = (-not $finished) -and ($out -match '(?im)usage limit')
    $apiError = (-not $finished) -and (-not $limit) -and ($out -match '(?m)^\s*API Error:')
    if ($apiError -and $attempt -lt 3) {
      "=== run $i hit a server error; retrying in 5 minutes (attempt $attempt of 3) ===" |
        Out-File -LiteralPath $log -Append -Encoding utf8
      Start-Sleep -Seconds 300
    }
  } while ($apiError -and $attempt -lt 3)

  "=== run $i ended $(Get-Date -Format s) ===" | Out-File -LiteralPath $log -Append -Encoding utf8
  if ($limit) {
    "=== usage limit reached; stopping ===" | Out-File -LiteralPath $log -Append -Encoding utf8
    break
  }
  if ($apiError) {
    "=== server errors persisted after 3 attempts; stopping ===" | Out-File -LiteralPath $log -Append -Encoding utf8
    break
  }
  $newWork = @(& git log --format=%s "$headBefore..HEAD" 2>$null | Where-Object { $_ -notmatch '^chore:' })
  if ($open -gt 0 -and (Open-Items) -eq $open -and $newWork.Count -eq 0) {
    "=== run $i made no progress (nothing built, open count unchanged); stopping ===" | Out-File -LiteralPath $log -Append -Encoding utf8
    break
  }
  if ($open -eq 0 -and (Open-Items) -eq 0) {
    "=== run $i started empty and drafted nothing; stopping ===" | Out-File -LiteralPath $log -Append -Encoding utf8
    break
  }
}

"=== night ended $(Get-Date -Format s), $(Open-Items) items open ===" | Out-File -LiteralPath $log -Append -Encoding utf8


