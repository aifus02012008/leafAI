import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { openChat } from './chatEvents';

/** Old /assistant links: open the floating chat on top of the dashboard. */
export function AssistantRedirect() {
  useEffect(() => {
    // Defer (no cleanup): this route unmounts right away and the chat listener mounts after it.
    window.setTimeout(openChat, 0);
  }, []);
  return <Navigate to="/dashboard" replace />;
}
