from locust import HttpUser, between, task


class ImperialUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        """
        Login como admin al iniciar.
        En producción esto debería usar un usuario de pruebas.
        """
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@imperial.local",
                "password": "ChangeMe123!",
            },
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
            }
        else:
            self.token = None
            self.headers = {}

    @task(5)
    def health(self):
        self.client.get("/health")

    @task(10)
    def get_carta(self):
        self.client.get("/api/v1/carta")

    @task(3)
    def list_tables(self):
        if self.token:
            self.client.get(
                "/api/v1/admin/mesas",
                headers=self.headers,
            )

    @task(2)
    def list_orders(self):
        if self.token:
            self.client.get(
                "/api/v1/admin/ordenes",
                headers=self.headers,
            )

    @task(1)
    def report_summary(self):
        if self.token:
            self.client.get(
                "/api/v1/admin/reportes/resumen",
                headers=self.headers,
            )
