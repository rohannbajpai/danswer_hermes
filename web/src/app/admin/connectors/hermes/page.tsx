"use client";

import * as Yup from "yup";
import { HermesIcon, TrashIcon } from "@/components/icons/icons";
import { TextFormField } from "@/components/admin/connectors/Field";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { CredentialForm } from "@/components/admin/connectors/CredentialForm";
import {
  Credential,
  ConnectorIndexingStatus,
  HermesConfig,
  HermesCredentialJson,
} from "@/lib/types";
import useSWR, { useSWRConfig } from "swr";
import { fetcher } from "@/lib/fetcher";
import { LoadingAnimation } from "@/components/Loading";
import { adminDeleteCredential, linkCredential } from "@/lib/credential";
import { ConnectorForm } from "@/components/admin/connectors/ConnectorForm";
import { ConnectorsTable } from "@/components/admin/connectors/table/ConnectorsTable";
import { usePopup } from "@/components/admin/connectors/Popup";
import { usePublicCredentials } from "@/lib/hooks";
import { AdminPageTitle } from "@/components/admin/Title";
import { Card, Text, Title } from "@tremor/react";

const Main = () => {
  const { popup, setPopup } = usePopup();

  const { mutate } = useSWRConfig();
  const {
    data: connectorIndexingStatuses,
    isLoading: isConnectorIndexingStatusesLoading,
    error: isConnectorIndexingStatusesError,
  } = useSWR<ConnectorIndexingStatus<any, any>[]>(
    "/api/manage/admin/connector/indexing-status",
    fetcher
  );

  const {
    data: credentialsData,
    isLoading: isCredentialsLoading,
    isValidating: isCredentialsValidating,
    error: isCredentialsError,
    refreshCredentials,
  } = usePublicCredentials();

  if (
    isConnectorIndexingStatusesLoading ||
    isCredentialsLoading ||
    isCredentialsValidating
  ) {
    return <LoadingAnimation text="Loading" />;
  }

  if (isConnectorIndexingStatusesError || !connectorIndexingStatuses) {
    return <div>Failed to load connectors</div>;
  }

  if (isCredentialsError || !credentialsData) {
    return <div>Failed to load credentials</div>;
  }

  const hermesConnectorIndexingStatuses: ConnectorIndexingStatus<
    HermesConfig,
    HermesCredentialJson
  >[] = connectorIndexingStatuses.filter(
    (connectorIndexingStatus: any) =>
      connectorIndexingStatus.connector.source === "hermes"
  );
  const hermesCredential: Credential<HermesCredentialJson> =
    credentialsData.filter(
      (credential: any) => credential.credential_json?.hermes_access_token
    )[0];

  return (
    <>
      {popup}
      <Text>
        This connector allows you to sync all your Hermes Tickets into Danswer.
      </Text>

      <Title className="mb-2 mt-6 ml-auto mr-auto">
        Step 1: Provide your Credentials
      </Title>

      {hermesCredential ? (
        <>
          <div className="flex mb-1 text-sm">
            <Text className="my-auto">Existing Access Token: </Text>
            <Text className="ml-1 italic my-auto max-w-md truncate">
              {hermesCredential.credential_json?.hermes_access_token}
            </Text>
            <button
              className="ml-1 hover:bg-hover rounded p-1"
              onClick={async () => {
                if (hermesConnectorIndexingStatuses.length > 0) {
                  setPopup({
                    type: "error",
                    message:
                      "Must delete all connectors before deleting credentials",
                  });
                  return;
                }
                await adminDeleteCredential(hermesCredential.id);
                refreshCredentials();
              }}
            >
              <TrashIcon />
            </button>
          </div>
        </>
      ) : (
        <>
          <Text>
            To use the Hermes connector, provide the Hermes Access Token.
          </Text>
          <Card className="mt-4">
            <CredentialForm<HermesCredentialJson>
              formBody={
                <>
                  <TextFormField
                    name="hermes_access_token"
                    label="Hermes Access Token:"
                    type="password"
                  />
                </>
              }
              validationSchema={Yup.object().shape({
                hermes_access_token: Yup.string().required(
                  "Please enter your Hermes Access Token"
                ),
              })}
              initialValues={{
                hermes_access_token: "",
              }}
              onSubmit={(isSuccess) => {
                if (isSuccess) {
                  refreshCredentials();
                }
              }}
            />
          </Card>
        </>
      )}

      <Title className="mb-2 mt-6 ml-auto mr-auto">
        Step 2: Start indexing!
      </Title>
      {hermesCredential ? (
        !hermesConnectorIndexingStatuses.length ? (
          <>
            <Text className="mb-2">
              Click the button below to start indexing! We will pull the latest
              tickets from Hermes every <b>10</b> minutes.
            </Text>
            <div className="flex">
              <ConnectorForm<HermesConfig>
                nameBuilder={() => "HermesConnector"}
                ccPairNameBuilder={() => "HermesConnector"}
                source="hermes"
                inputType="poll"
                formBody={null}
                validationSchema={Yup.object().shape({})}
                initialValues={{}}
                refreshFreq={10 * 60} // 10 minutes
                credentialId={hermesCredential.id}
              />
            </div>
          </>
        ) : (
          <>
            <Text className="mb-2">
              Hermes connector is setup! We are pulling the latest tickets from
              Hermes every <b>10</b> minutes.
            </Text>
            <ConnectorsTable<HermesConfig, HermesCredentialJson>
              connectorIndexingStatuses={hermesConnectorIndexingStatuses}
              liveCredential={hermesCredential}
              getCredential={(credential) => {
                return (
                  <div>
                    <p>{credential.credential_json.hermes_access_token}</p>
                  </div>
                );
              }}
              onCredentialLink={async (connectorId) => {
                if (hermesCredential) {
                  await linkCredential(connectorId, hermesCredential.id);
                  mutate("/api/manage/admin/connector/indexing-status");
                }
              }}
              onUpdate={() =>
                mutate("/api/manage/admin/connector/indexing-status")
              }
            />
          </>
        )
      ) : (
        <>
          <Text>
            Please provide your access token in Step 1 first! Once done with
            that, you can then start indexing all your Hermes tickets.
          </Text>
        </>
      )}
    </>
  );
};

export default function Page() {
  return (
    <div className="mx-auto container">
      <div className="mb-4">
        <HealthCheckBanner />
      </div>

      <AdminPageTitle icon={<HermesIcon size={32} />} title="Hermes" />

      <Main />
    </div>
  );
}
