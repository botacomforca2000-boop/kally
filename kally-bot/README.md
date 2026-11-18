# Kally Bot

Bot de Discord em Python (discord.py 2.x), 100% slash commands.

## Funções
Moderação • Logs • Anti-raid • Níveis/XP • Economia • Tickets • VIP (com expiração) • Instagram (feed com likes)

## Como rodar
1. Crie o bot em https://discord.com/developers/applications
   - Aba **Bot** → ative **Server Members Intent**
   - Convide com os escopos `bot` + `applications.commands` e permissões de Administrador (ou as necessárias)
2. `pip install -r requirements.txt`
3. Copie `.env.example` para `.env` e coloque o token
4. `python main.py`
5. No servidor, configure com `/config ver`, `/config logs`, `/config vip`, `/config ticket`, `/config insta`, `/config niveis`, `/config antiraid`
6. Use `/ticket painel` no canal onde quer o botão de tickets

O cargo da Kally precisa estar **acima** dos cargos que ela vai gerenciar (VIP, membros punidos).
