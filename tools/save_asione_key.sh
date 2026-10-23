#!/bin/zsh
# Prompt for an ASI:One API key without echoing it and store it in ~/omega-runtime/.env (mode 600),
# outside the repository so it can never be committed.
read -rs "key?Paste your ASI:One API key and press Enter (input is hidden): "
echo
if [[ -z "$key" ]]; then
  echo "No key entered; nothing saved."
  exit 1
fi
mkdir -p ~/omega-runtime
umask 077
printf 'ASIONE_API_KEY=%s\n' "$key" > ~/omega-runtime/.env
chmod 600 ~/omega-runtime/.env
unset key
echo "Saved to ~/omega-runtime/.env (only your user can read it)."
