import React from 'react';
import PropTypes from 'prop-types';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faCheckCircle,
  faExclamationTriangle,
  faInfoCircle,
  faTimesCircle,
} from '@fortawesome/free-solid-svg-icons';

const icons = {
  success: faCheckCircle,
  warning: faExclamationTriangle,
  info: faInfoCircle,
  error: faTimesCircle,
};

const Alert = ({ type = 'info', message = '' }) => {
  return (
    <div className={`alert alert-${type}`}>
      <FontAwesomeIcon icon={icons[type]} />
      <span>{message}</span>
    </div>
  );
};

Alert.propTypes = {
  type: PropTypes.oneOf(['success', 'warning', 'info', 'error']),
  message: PropTypes.string.isRequired,
};

export default Alert;
