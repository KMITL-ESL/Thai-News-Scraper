CREATE TABLE public.raw_news
(
    id uuid NOT NULL,
    publish_date date,
    title text,
    content text,
    created_at date NOT NULL,
    source character varying(256) NOT NULL,
    link character varying(256) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE public.raw_news
    OWNER to postgres;