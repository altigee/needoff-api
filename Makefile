.PHONY: db.start
db.start:
	docker-compose up -d

.PHONY: db.stop
db.stop:
	docker-compose down
