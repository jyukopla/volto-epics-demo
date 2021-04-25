import React from 'react';
import { Button, Grid } from 'semantic-ui-react';
import { FormattedMessage } from 'react-intl';
import { Container } from 'semantic-ui-react';
import { Redirect } from 'react-router-dom';
import { useHistory } from 'react-router';
import { EPICS_PATH_CONTINUE } from 'volto-epics-addon/constants';
import { cancelEpic } from 'volto-epics-addon/helpers';

const Page = ({ match }) => {
  const history = useHistory();
  const errorToken = match.params.uuid;
  return errorToken ? (
    <Container style={{ margin: '2em 0' }}>
      <Grid stackable centered stretched verticalAlign="middle">
        <Grid.Row>
          <Grid.Column className="grid-column-content" width={8}>
            <h2>
              <FormattedMessage
                id="processUnexpectedError"
                defaultMessage="Unexpected error"
              />
            </h2>
            <p>We are very sorry, but an unexpected error has occurred.</p>
            <p>
              When contacting support, please, pass along the following details:
            </p>
            <p>Error id: {errorToken || 'n/a'}</p>
          </Grid.Column>
        </Grid.Row>
        <Grid.Row>
          <Grid.Column className="grid-column-content" width={4}>
            <Button onClick={() => history.push(EPICS_PATH_CONTINUE)}>
              Try again
            </Button>
          </Grid.Column>
          <Grid.Column className="grid-column-content" width={4}>
            <Button onClick={cancelEpic}>Give up</Button>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    </Container>
  ) : (
    <Redirect
      to={{
        pathname: '/',
      }}
    />
  );
};

export default Page;
