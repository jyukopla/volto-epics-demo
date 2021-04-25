import React, {useEffect, useState} from 'react';
import { Button, Form, Grid } from 'semantic-ui-react';
import { useTask, completeTask, sendMessage } from 'volto-epics-addon/helpers';
import { WPD_TASK_CREATE_EVENT } from '../constants';
import { useIntl } from 'react-intl';
import DatetimeWidget from '@plone/volto/components/manage/Widgets/DatetimeWidget';

const EventFormPage = () => {
  const [creating, setCreating] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [payload, setPayload] = useState();
  const intl = useIntl();
  const task = useTask(WPD_TASK_CREATE_EVENT);

  useEffect(() => {
    (async () => {
      setPayload({
        ...payload,
        ...(task?.variables ?? {}),
      });
    })();
  }, [task]);
  return (
    <Grid centered>
      <Grid.Row>
        <Grid.Column className="grid-column-content" width={8}>
          <h2>Create new event</h2>
          <Form>
            <Form.Input
              id="title"
              label="Title"
              value={payload?.title ?? ''}
              onChange={(e) => {
                setPayload({
                  ...payload,
                  title: e.target.value,
                });
              }}
            />
            <Form.TextArea
              id="description"
              label="Description"
              value={payload?.description ?? ''}
              onChange={(e) => {
                setPayload({
                  ...payload,
                  description: e.target.value,
                });
              }}
            />
            <Form.Field
              id="start"
              title="Start"
              control={DatetimeWidget}
              intl={intl}
              value={payload?.start ?? null}
              onChange={(name, value) => {
                setPayload({
                  ...payload,
                  start: value,
                });
              }}
            />
            <Form.Field
              id="end"
              title="End"
              control={DatetimeWidget}
              intl={intl}
              value={payload?.end ?? null}
              onChange={(name, value) => {
                setPayload({
                  ...payload,
                  end: value,
                });
              }}
            />
          </Form>
          <Button
            primary
            disabled={
              canceling ||
              !(
                payload?.title &&
                payload?.description &&
                payload?.start &&
                payload?.end
              )
            }
            loading={creating}
            style={{ marginTop: '1em' }}
            onClick={async () => {
              setCreating(true);
              await completeTask(WPD_TASK_CREATE_EVENT, payload);
            }}
          >
            Create
          </Button>
          <Button
            disabled={creating}
            loading={canceling}
            style={{ marginTop: '1em' }}
            onClick={async () => {
              setCanceling(true);
              await sendMessage('create-event-cancel');
            }}
          >
            Cancel
          </Button>
        </Grid.Column>
      </Grid.Row>
    </Grid>
  );
};

export default EventFormPage;
