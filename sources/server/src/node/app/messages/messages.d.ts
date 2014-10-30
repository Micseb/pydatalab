/*
 * Copyright 2014 Google Inc. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */


/**
 * Internal message types for capturing the relevant details of the IPython messaging protocol
 *
 * Imminent changes to the messaging spec from protocol 4.1 to 5.x
 * https://github.com/ipython/ipython/wiki/IPEP-13:-Updating-the-Message-Spec
 */


declare module app {

  interface MessageProcessor {
    /**
     * @param message the message to process
     * @param session session object from which the message originated
     * @return the processed message or null to indicate message should be filtered
     */
    (message: any, session: app.ISession): any;
  }

  interface MessageHandler {
    (message: any, session: app.ISession, callback: app.EventHandler<any>): void
  }

  interface KernelStatus {
    status: string;
    requestId: string;
  }

  interface ExecuteReply {
    success: boolean;
    requestId: string;
    // When execute has not been aborted, we get back an execution count
    executionCount?: number;
    // When an error has occurred, the following are populated
    errorName?: string;
    errorMessage?: string;
    traceback?: string[];
  }

  interface ExecuteRequest {
    code: string;
    // Note: user_variables and user_expressions are slated for removal/reworking in upcoming versions
    // https://github.com/ipython/ipython/wiki/IPEP-13:-Updating-the-Message-Spec
    requestId: string;
  }

  interface ExecuteResult {
    result: any;
    requestId: string;
  }

  module ipy {

    interface Header {
      msg_id: string;
      msg_type: string;
    }

    interface Message {
      identities: string[];
      header: Header;
      parentHeader: Header;
      metadata: Map<any>;
      content: any;
    }

    interface ExecuteRequestContent {
      code: string;
      silent: boolean;
      store_history: boolean;
      allow_stdin: boolean;
    }
  }

}