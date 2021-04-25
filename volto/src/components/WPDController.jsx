import React, { useEffect } from 'react';
import { useHistory, useLocation } from 'react-router';
import { toast } from 'react-toastify';
import { Button, Grid } from 'semantic-ui-react';
import { startEpic, useContinuationPoll } from 'volto-epics-addon/helpers';
import {
  WORLD_PLONE_DAY,
  WPD_TASK_EVENTS,
  WPD_TASK_TIMEOUT,
} from '../constants';
import { completeTask } from 'volto-epics-addon/helpers';
import { EPICS_TASK_VIEWS } from 'volto-epics-addon/constants';

const CreateNewEventPrompt = () => {
  return (
    <Grid centered verticalAlign="middle" textAlign="center">
      <Grid.Row centered columns={1} style={{ padding: '1em 0 0.7em 0' }}>
        <Grid.Column>
          <p>Do you want to create a new event?</p>
          <p>
            <Button
              onClick={async () => {
                await completeTask(WPD_TASK_EVENTS, { create: true });
              }}
            >
              Yes
            </Button>
            <Button
              onClick={async () => {
                await completeTask(WPD_TASK_EVENTS, { create: false });
              }}
            >
              No
            </Button>
          </p>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
};

const WPDController = () => {
  const continuation = useContinuationPoll(true);
  const location = useLocation();
  const history = useHistory();

  useEffect(() => {
    if (
      continuation?.location?.pathname &&
      location.pathname !== continuation.location.pathname &&
      [EPICS_TASK_VIEWS[WPD_TASK_TIMEOUT]].includes(
        continuation.location.pathname,
      )
    ) {
      history.push(continuation.location.pathname);
    }
  }, [continuation, location]);

  const WPD_CONTROLLER_TOAST = 'wpd';

  useEffect(() => {
    if (
      continuation?.taskDefinitionKey === WPD_TASK_EVENTS &&
      location.pathname === '/events'
    ) {
      toast.success(<CreateNewEventPrompt />, {
        toastId: WPD_CONTROLLER_TOAST,
        closeOnClick: false,
        autoClose: false,
        closeButton: false,
      });
    } else {
      toast.dismiss(WPD_CONTROLLER_TOAST);
    }
  }, [continuation, location]);

  return (
    <div
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
      }}
    >
      <Button
        onClick={async () => {
          await startEpic(WORLD_PLONE_DAY, {});
        }}
        disabled={continuation?.location?.pathname !== '/'}
      >
        WPD
      </Button>
    </div>
  );
};

export default WPDController;
