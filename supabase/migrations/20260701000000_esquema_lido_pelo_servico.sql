-- Esquema mínimo que o serviço de recomendação lê, para subir um ambiente do zero.
-- Reconstruído a partir do código do serviço e dos modelos do app; não é o dump
-- do banco de produção do Gana (que tem mais tabelas e colunas).

create table if not exists public.users (
    id          uuid primary key references auth.users (id) on delete cascade,
    username    text unique,
    name        text,
    is_private  boolean not null default false,
    created_at  timestamptz not null default now()
);

create table if not exists public.book_cache (
    id               uuid primary key default gen_random_uuid(),
    created_at       timestamptz not null default now(),
    google_books_id  text not null unique,
    isbn             text,
    title            text not null,
    author           text[] not null default '{}',
    pages            integer not null default 0,
    year_published   integer,
    publisher        text,
    description      text,
    main_category    text,
    categories       text[] not null default '{}',
    language         text not null default 'pt',
    url_image        text
);

create table if not exists public.user_book (
    id               uuid primary key default gen_random_uuid(),
    created_at       timestamptz not null default now(),
    id_user          uuid not null references public.users (id) on delete cascade,
    google_books_id  text not null references public.book_cache (google_books_id),
    status           text not null check (status in ('Quero ler', 'Lendo', 'Lido', 'Abandonado')),
    begin_date       date,
    finish_date      date,
    unique (id_user, google_books_id)
);

alter table public.users enable row level security;
alter table public.book_cache enable row level security;
alter table public.user_book enable row level security;

-- o app lê o catálogo e mexe só nas próprias linhas; o serviço usa a service_role
create policy "catálogo legível por quem está logado" on public.book_cache
    for select to authenticated using (true);
create policy "cada pessoa vê o próprio perfil" on public.users
    for select to authenticated using (id = auth.uid());
create policy "cada pessoa gerencia a própria estante" on public.user_book
    for all to authenticated using (id_user = auth.uid()) with check (id_user = auth.uid());

grant select on public.users, public.book_cache, public.user_book to service_role;
grant insert, update on public.book_cache to service_role;  -- gana ingest
