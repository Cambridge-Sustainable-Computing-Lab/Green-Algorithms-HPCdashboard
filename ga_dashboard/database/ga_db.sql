--
-- PostgreSQL database dump
--

-- Dumped from database version 13.13
-- Dumped by pg_dump version 13.13

--
-- Example usage:
--
-- % cd GA4HPCdashboard/database
-- % psql -U postgres
-- # drop database ga_db;
-- # create database ga_db;
-- # \q
-- % psql -U postgres -d ga_db < ga_db.sql
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ga_data_aggregate; Type: TABLE; Schema: public; Owner: -
--

DROP TABLE IF EXISTS public.ga_data_aggregate; -- Needed due to postgres caching

CREATE TABLE public.ga_data_aggregate (
    user_name character varying(255),
    submitdate date,
    n_jobs integer,
    first_job_period date,
    last_job_period date,
    energy double precision,
    energy_cpus double precision,
    energy_gpus double precision,
    energy_memory double precision,
    carbonfootprint double precision,
    carbonfootprint_memoryneededonly double precision,
    carbonfootprint_failedjobs double precision,
    cputime character varying(255),
    gputime character varying(255),
    wallclocktime character varying(255),
    cpuhourscharged double precision,
    gpuhourscharged double precision,
    memoryrequested double precision,
    memoryoverallocationfactor double precision,
    n_success integer,
    treemonths double precision,
    treemonths_memoryneededonly double precision,
    treemonths_failedjobs double precision,
    driving double precision,
    flying_ny_sf double precision,
    flying_par_lon double precision,
    flying_nyc_mel double precision,
    cost double precision,
    cost_failedjobs double precision,
    cost_memoryneededonly double precision,
    success_rate double precision,
    failure_rate double precision,
    share_carbonfootprint double precision
);


--
-- Name: ga_data_aggregate ga_data_aggregate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ga_data_aggregate
    ADD CONSTRAINT ga_data_aggregate_pkey PRIMARY KEY (user_name, submitdate);


--
-- Name: ga_user; Type: TABLE; Schema: public; Owner: -
--

DROP TABLE IF EXISTS public.ga_user;

CREATE TABLE public.ga_user (
    user_name character varying(255),
    uid integer,
    name character varying(255),
    group_name character varying(255),
    department character varying(255),
    updated TIMESTAMP DEFAULT now()
);


--
-- Name: ga_user ga_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ga_user
    ADD CONSTRAINT ga_user_pkey PRIMARY KEY (user_name);

--
-- Name: ga_unfinished_jobs; Type: TABLE; Schema: public; Owner: -
--

DROP TABLE IF EXISTS public.ga_unfinished_jobs; -- Needed due to postgres caching

CREATE TABLE public.ga_unfinished_jobs (
    job_id character varying(255),
    user_name character varying(255),
    submitdate date,
    startdate date,
    job_state character varying(255)
);


--
-- Name: ga_data_aggregate ga_data_aggregate_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ga_unfinished_jobs
    ADD CONSTRAINT ga_unfinished_jobs_pkey PRIMARY KEY (job_id);


--
-- PostgreSQL database dump complete
--

