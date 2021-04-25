import React from 'react';
import { Button, Container, Grid } from 'semantic-ui-react';
import { WPD_TASK_WELCOME } from '../constants';
import { completeTask } from 'volto-epics-addon/helpers';

const WelcomePage = () => {
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
              <h2>Welcome to World Plone Day!</h2>
              <p>This demonstration is being directed by BPMN.</p>
              <p>
                <Button
                  primary
                  onClick={async () => {
                    await completeTask(WPD_TASK_WELCOME);
                  }}
                >
                  Continue
                </Button>
              </p>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Container>
    </>
  );
};

export default WelcomePage;
