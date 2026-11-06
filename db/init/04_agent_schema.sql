CREATE SCHEMA agent;

CREATE TABLE agent.conversation (
    id uuid PRIMARY KEY,
    person_id text NOT NULL REFERENCES sag.person (person_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX conversation_person_recent ON agent.conversation (person_id, updated_at DESC);

CREATE TABLE agent.message (
    id uuid PRIMARY KEY,
    conversation_id uuid NOT NULL REFERENCES agent.conversation (id),
    position integer NOT NULL,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL DEFAULT '',
    model text,
    tokens_in integer,
    tokens_out integer,
    latency_ms integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, position)
);

CREATE TABLE agent.tool_call (
    message_id uuid NOT NULL REFERENCES agent.message (id),
    id text NOT NULL,
    position integer NOT NULL,
    name text NOT NULL,
    arguments jsonb NOT NULL,
    result jsonb,
    status text NOT NULL,
    duration_ms integer,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (message_id, id)
);

CREATE SEQUENCE agent.protocol_number_seq;
CREATE SEQUENCE agent.protocol_interaction_seq;

SELECT setval('agent.protocol_number_seq', (SELECT max(protocol::bigint) FROM secretary.protocol));
SELECT setval(
    'agent.protocol_interaction_seq',
    (SELECT max(interaction_id::bigint) FROM secretary.protocol_interaction)
);
