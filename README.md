# Dev Amp — Agent Pipeline

Agenci i skille dla Dev Amp pipeline.

## Instalacja

```bash
# Agenci → ~/.claude/agents/
cp agents/*.md ~/.claude/agents/

# Skille → ~/.claude/skills/
cp -r skills/* ~/.claude/skills/
```

## Pipeline

```
Discovery → Product → Dev-System → Dev-Multi → Dev-Single → QA
```

## Agenci

| Agent | Rola |
|-------|------|
| `discovery` | Wyłania wizję produktu z rozmowy z developerem/klientem |
| `product` | Analiza produktowa, spec, UX |
| `developer-system` | Analiza impactu systemowego |
| `developer-multi` | Koordynacja między projektami |
| `developer-single` | Implementacja kodu |
| `qa` | Testowanie, zbieranie bugów, routing |

## Skille

| Skill | Opis |
|-------|------|
| `ui-ux` | Generyczny skill UI/UX — checklist per rola (product/dev/qa) |
