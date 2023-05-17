{{/*
Expand the name of the chart.
*/}}
{{- define "eoapi.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "eoapi.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "eoapi.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "eoapi.labels" -}}
helm.sh/chart: {{ include "eoapi.chart" . }}
{{ include "eoapi.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "eoapi.selectorLabels" -}}
app.kubernetes.io/name: {{ include "eoapi.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "eoapi.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "eoapi.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
######################## VALIDATORS #######################################
*/}}
{{/* Compile all validation warnings into a single message and call fail. */}}
{{- define "eoapi.validateValues" -}}
{{- $messages := list -}}
{{- $messages = append $messages (include "eoapi.validateValues.db.environment" .) -}}
{{- $messages = append $messages (include "eoapi.validateValues.pguser" .) -}}
{{- $messages = append $messages (include "eoapi.validateValues.postgres_user" .) -}}
{{- $messages = append $messages (include "eoapi.validateValues.pgpassword" .) -}}
{{- $messages = append $messages (include "eoapi.validateValues.postgres_password" .) -}}
{{- $messages = append $messages (include "eoapi.validateValues.gitsha" .) -}}
{{- $messages = without $messages "" -}}
{{- $message := join "\n" $messages -}}
{{- if $message -}}
{{- printf "\nVALUES VALIDATION:\n%s" $message | fail -}}
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.db.environment" -}}
{{- if not (or (eq .Values.db.environment "k8s") (eq .Values.db.environment "rds")) -}}
db:
  environment: "{{ .Values.db.environment }}" <<<
  `environment` is required and should be a non-empty string of "k8s" || "rds"
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.pgpassword" -}}
{{- if not (and .Values.db.settings.secrets.PGPASSWORD (kindIs "string" .Values.db.settings.secrets.PGPASSWORD)) -}}
DB_SETTINGS:
  PGPASSWORD: "{{ .Values.db.settings.secrets.PGPASSWORD }}" <<<
  `PGPASSWORD` is required and should be a non-empty string
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.pguser" -}}
{{- if not (and .Values.db.settings.secrets.PGUSER (kindIs "string" .Values.db.settings.secrets.PGUSER)) -}}
DB_SETTINGS:
  PGUSER: "{{ .Values.db.settings.secrets.PGUSER }}" <<<
  `PGUSER` is required and should be a non-empty string
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.postgres_password" -}}
{{- if not (and .Values.db.settings.secrets.POSTGRES_PASSWORD (kindIs "string" .Values.db.settings.secrets.POSTGRES_PASSWORD)) -}}
DB_SETTINGS:
  POSTGRES_PASSWORD: "{{ .Values.db.settings.secrets.POSTGRES_PASSWORD }}" <<<
  `POSTGRES_PASSWORD` is required and should be a non-empty string
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.postgres_user" -}}
{{- if not (and .Values.db.settings.secrets.POSTGRES_USER (kindIs "string" .Values.db.settings.secrets.POSTGRES_USER)) -}}
DB_SETTINGS:
  POSTGRES_USER: "{{ .Values.db.settings.secrets.POSTGRES_USER }}" <<<
  `POSTGRES_USER` is required and should be a non-empty string
{{- end -}}
{{- end -}}

{{- define "eoapi.validateValues.gitsha" -}}
{{- if not (and .Values.gitSha (kindIs "string" .Values.gitSha)) -}}
gitSha: "{{ .Values.gitSha }}" <<<
  `gitSha` is required and should be a non-empty string
{{- end -}}
{{- end -}}
