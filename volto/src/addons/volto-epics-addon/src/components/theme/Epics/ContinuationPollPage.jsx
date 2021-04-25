import React, { useEffect, useState } from 'react';
import { FormattedMessage } from 'react-intl';
import { useHistory } from 'react-router';
import { Button, Container, Grid } from 'semantic-ui-react';
import { Helmet } from '@plone/volto/helpers';
import { sendMessage, useContinuationPoll } from 'volto-epics-addon/helpers';
import { BarLoader } from 'react-spinners';
import { EPICS_PATH_CONTINUE } from 'volto-epics-addon/constants';

const ContinuationPollPage = () => {
  const history = useHistory();
  const continuation = useContinuationPoll();
  const [cancellable, setCancellable] = useState(false);

  useEffect(() => {
    if (continuation?.location?.pathname) {
      if (continuation.location.pathname !== EPICS_PATH_CONTINUE) {
        history.push(continuation.location.pathname);
      }
    }
    if ((continuation?.counter ?? 0) > 3) {
      setCancellable(true);
    }
  }, [continuation]);

  return (
    <>
      <Helmet title={'Please wait…'} />
      <Container
        style={{
          display: 'flex',
          justifyContent: 'center',
          height: '100%',
          alignItems: 'center',
        }}
      >
        <Grid stackable centered stretched verticalAlign="middle">
          <Grid.Row>
            <Grid.Column
              className="grid-column-content"
              width={8}
              textAlign="center"
            >
              <h2>
                <FormattedMessage
                  id="processPleaseWait"
                  defaultMessage="Please wait…"
                />
              </h2>
              {continuation?.statusMessage ? (
                <p>{continuation.statusMessage}</p>
              ) : (
                <p>We are currently processing your request.</p>
              )}
            </Grid.Column>
          </Grid.Row>
          <Grid.Row>
            <Grid.Column
              className="grid-column-content"
              width={8}
              textAlign="center"
              id="bar-loader-column"
            >
              <BarLoader width={200} />
            </Grid.Column>
          </Grid.Row>
          {cancellable && !continuation?.statusMessage ? (
            <Grid.Row>
              <Grid.Column
                textAlign="center"
                className="grid-column-content"
                width={8}
              >
                <p>We are sorry, but this is taking longer than expected.</p>
                <Button
                  onClick={() => {
                    sendMessage('cancel');
                  }}
                >
                  Give up
                </Button>
              </Grid.Column>
            </Grid.Row>
          ) : null}
        </Grid>
      </Container>
    </>
  );
};

export default ContinuationPollPage;
