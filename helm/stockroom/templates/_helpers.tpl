{{/* The short name of the chart. */}}
{{- define "stockroom.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* The full name of the release. */}}
{{- define "stockroom.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/* The labels of every object. */}}
{{- define "stockroom.labels" -}}
app.kubernetes.io/name: {{ include "stockroom.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* The selector labels of one component. The component name is the argument. */}}
{{- define "stockroom.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stockroom.name" .root }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{/* The name of the database secret. */}}
{{- define "stockroom.secretName" -}}
{{- printf "%s-db" (include "stockroom.fullname" .) -}}
{{- end -}}

{{/* The connection string of the database. */}}
{{- define "stockroom.databaseUrl" -}}
{{- printf "postgresql+psycopg://%s:%s@%s-postgres:%v/%s" .Values.postgres.auth.username .Values.postgres.auth.password (include "stockroom.fullname" .) .Values.postgres.service.port .Values.postgres.auth.database -}}
{{- end -}}
