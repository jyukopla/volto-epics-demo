// ButtonLink/index.jsx
import React from 'react';
import { Button } from 'semantic-ui-react';
import './style.css';

const ButtonLink = ({ className = '', ...props }) => (
  <Button
    basic
    color="blue"
    className={['link', className].join(' ')}
    {...props}
  />
);

export default ButtonLink;
