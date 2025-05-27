import React from 'react'

function Settings({active}) {

  if (!active) return null;
  
    return (
        <div>
           <h1>Setting Komponent</h1>
        </div>
    )
}

export default Settings
