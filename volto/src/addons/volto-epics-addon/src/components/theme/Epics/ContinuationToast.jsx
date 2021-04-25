import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { Button, Grid } from 'semantic-ui-react';

import { EPIC_TOAST_CONTINUATION } from 'volto-epics-addon/constants';
import ButtonLink from 'volto-epics-addon/components/theme/ButtonLink/ButtonLink';

const ContinuationToast = (props) => {
  const { type, onContinue, onCancel, title, content } = props;

  const [confirmCancel, setConfirmCancel] = useState(false);
  const [loading, setLoading] = useState(false);

  const cancelLink = confirmCancel ? (
    <Button
      className="toast-button"
      loading={loading}
      onClick={async (e) => {
        if (!loading) {
          setLoading(true);
          await onCancel(e);
        }
      }}
    >
      <div className="toast-button-content">
        <span className="toast-button-text">Yes, cancel</span>
      </div>
    </Button>
  ) : (
    <Button className="toast-button" onClick={() => setConfirmCancel(true)}>
      <div className="toast-button-content">
        <span className="toast-button-text">Cancel</span>
      </div>
    </Button>
  );

  const continueLink = confirmCancel ? (
    <Button
      className="toast-button"
      disabled={loading}
      onClick={() => {
        setLoading(true);
        toast.dismiss(EPIC_TOAST_CONTINUATION);
      }}
    >
      <div className="toast-button-content">
        <span className="toast-button-text">No, continue</span>
      </div>
    </Button>
  ) : (
    <Button className="toast-button" onClick={onContinue}>
      <div className="toast-button-content">
        <span className="toast-button-text">continue</span>
      </div>
    </Button>
  );

  return (
    <>
      <Grid className="toast-grid-container" textAlign="center">
        <>
          <Grid.Row style={{ padding: '1em 0 0.7em 0' }}>
            <Grid.Column>
              <Grid>
                {!onCancel || !!props.error ? (
                  <Grid.Row>
                    <Grid.Column>
                      <h4>{title}</h4>
                    </Grid.Column>
                  </Grid.Row>
                ) : null}
                {!!onCancel || type === 'continue' || content ? (
                  <Grid.Row
                    style={
                      !!onContinue || (!!onCancel && confirmCancel)
                        ? {
                            padding: '0.3em 0 0.6em 0px',
                          }
                        : null
                    }
                  >
                    <Grid.Column>
                      {type === 'continue' ? (
                        <p style={{ color: '#012957' }}>
                          Click continue to proceed previous action or cancel
                          it.
                        </p>
                      ) : !!onCancel ? (
                        confirmCancel ? (
                          <p style={{ color: '#012957' }}>
                            Do you really want to cancel?
                          </p>
                        ) : (
                          <p style={{ color: '#012957' }}>
                            If you don't want to continue, please click{' '}
                            <ButtonLink onClick={() => setConfirmCancel(true)}>
                              cancel
                            </ButtonLink>
                            {'.'}
                          </p>
                        )
                      ) : (
                        <>{content && <p>{content}</p>}</>
                      )}
                    </Grid.Column>
                  </Grid.Row>
                ) : null}
                {(!!onContinue || (!!onCancel && confirmCancel)) && (
                  <Grid.Row
                    columns={!!onCancel ? 'equal' : '1'}
                    textAlign="center"
                    style={{ padding: '0.4em 0 0.8em 0' }}
                  >
                    {!!onContinue && <Grid.Column>{continueLink}</Grid.Column>}
                    {!!onCancel && confirmCancel && (
                      <>
                        <Grid.Column>{cancelLink}</Grid.Column>
                        <Grid.Column>{continueLink}</Grid.Column>
                      </>
                    )}
                  </Grid.Row>
                )}
              </Grid>
            </Grid.Column>
          </Grid.Row>
        </>
      </Grid>
    </>
  );
};

export default ContinuationToast;
