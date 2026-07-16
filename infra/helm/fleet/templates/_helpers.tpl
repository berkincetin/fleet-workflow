{{- define "fleet.namespace" -}}
{{- .Values.namespace | default "fleet" -}}
{{- end -}}
