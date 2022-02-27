#!/bin/bash
read -p "Enter a number > " number

for ((i = 1; i <= number; i++)); do
  UUID=$(uuidgen)

  URL="https://www.4devs.com.br/ferramentas_online.php"

  RESPONSE=$(curl -s -w "%{http_code}" $URL \
               --header 'Content-Type: application/x-www-form-urlencoded' \
               --data-urlencode 'acao=gerar_pessoa' \
               --data-urlencode 'txt_qtde=1')

  END_CONTENT=${#RESPONSE}
  HTTP_CODE=${RESPONSE: -3}
  CONTENT=$(echo "${RESPONSE:0:END_CONTENT-3}")

  if [ "$HTTP_CODE" = 200 ]; then
    CPF=$(echo "$CONTENT" | jq -r '.[0].cpf')
    NAME=$(echo "$CONTENT" | jq -r '.[0].nome')

    echo "$CPF"
    echo "$NAME"
    JSON=$(jq \
        --arg employeeId "$UUID" \
        --arg cpf "$CPF" \
        --arg name "$NAME" \
        '.contents.employeeId = $employeeId | .contents.cpf = $cpf | .contents.name = $name' \
        './json-file')

    awslocal --endpoint-url=http://localhost:4566 sns publish --topic-arn arn:aws:sns:us-east-1:000000000000:QUEUE_NAME --message "$JSON" --cli-connect-timeout 60000
#    aws --endpoint-url=https://sns.sa-east-1.amazonaws.com/ sns publish --topic-arn arn:aws:sns:sa-east-1:739171219021:QUEUE_NAME --message "$JSON" --cli-connect-timeout 60000
  fi
done
