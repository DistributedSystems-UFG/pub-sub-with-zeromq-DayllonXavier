# Pub-Sub-Basics-with-ZeroMQ

Implementação de um sistema de chat com suporte a mensagens individuais entre usuários e mensagens direcionadas para grupos de usuários. Software foi desevolvido com a biblioteca ZeroMQ e utilizando a abordagem pub-sub para o envio e recebimento de mensagens de grupos. 

O arquivo "const.py" contém o IP e a porta do servidor.

O arquivo "server.py" é o código referente ao servidor que recebe as requisições do usuário..

O arquivo "user.py" é  o código referente ao usuário da aplicação. 

Tipos de operações suportadas pelo usuário:

	- REGISTER \<group\> 
	- LEAVE \<group\> 
	- PUB \<group\> \<message\>
	- TO \<user\> \<message\>
	

# Vídeo da apresentação
O link para a apresentação do projeto, onde é exposto mais detalhes da sua implementação e do seu funcionamento, está disponível aqui: https://youtu.be/7JpHc5RLaC8
