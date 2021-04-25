import React, { useEffect } from 'react';
import { Container, Grid } from 'semantic-ui-react';
import { completeTask } from '../addons/volto-epics-addon/src/helpers';
import { WPD_TASK_THANKS } from '../constants';

const TimeoutPage = () => {
  useEffect(() => {
    setTimeout(async () => {
      await completeTask(WPD_TASK_THANKS);
    }, 5000);
  }, []);
  return (
    <>
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
              width={12}
              textAlign="center"
            >
              <h2>Thank you!</h2>
              <p>
                This demo is now complete and you are being redirected back to
                the front page.
              </p>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Container>
    </>
  );
};

export default TimeoutPage;
