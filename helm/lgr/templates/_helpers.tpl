{{/* Print region if defined */}}
{{- define "lgr.region" -}}
  {{- if .region -}}
    {{- printf "%s-" .region -}}
  {{- end -}}
{{- end -}}
