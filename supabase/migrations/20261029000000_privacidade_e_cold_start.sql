-- Specs 003 e 005: gêneros do onboarding, consentimentos, data de nascimento e
-- classificação etária dos livros.

alter table public.users
    add column if not exists birth_date date,
    -- base legal: consentimento (LGPD art. 7º, I). Começa desligado (opt-in).
    add column if not exists personalization_consent boolean not null default false,
    -- menores de 12 anos: consentimento específico de um responsável (art. 14, §1º)
    add column if not exists parental_consent boolean not null default false,
    add column if not exists favorite_genres text[] not null default '{}';

comment on column public.users.personalization_consent is
    'Consentimento para recomendações personalizadas. Sem ele, o serviço só usa popularidade e não treina com as leituras da pessoa.';
comment on column public.users.birth_date is
    'Usada só para a faixa etária (filtro de conteúdo e regra de crianças). Nunca sai do serviço.';

alter table public.book_cache
    add column if not exists maturity_rating text not null default 'NOT_MATURE'
        check (maturity_rating in ('MATURE', 'NOT_MATURE'));

-- a pessoa pode ver e alterar os próprios consentimentos e gêneros pelo app
create policy "cada pessoa atualiza o próprio perfil" on public.users
    for update to authenticated using (id = auth.uid()) with check (id = auth.uid());
