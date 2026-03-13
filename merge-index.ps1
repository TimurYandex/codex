param(
  [string]$Output = "index.html",
  [string]$PartsDir = "parts"
)

$parts = Get-ChildItem -Path $PartsDir -Filter "index.part*.txt" | Sort-Object Name
if (-not $parts) {
  throw "No part files found in '$PartsDir'."
}

$content = ""
foreach ($p in $parts) {
  $content += Get-Content -Raw -Path $p.FullName
}

Set-Content -Path $Output -Value $content -Encoding UTF8 -NoNewline
Write-Host "Merged $($parts.Count) parts into $Output"
