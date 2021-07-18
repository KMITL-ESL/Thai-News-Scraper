CREATE TABLE public.raw_news
(
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 9999999999 CACHE 1 ),
    publish_date timestamp without time zone,
    title text,
    content text,
    created_at timestamp without time zone,
    source character varying(256) NOT NULL,
    link character varying(256) NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT "link unique" UNIQUE (link)
);

ALTER TABLE public.raw_news
    OWNER to postgres;