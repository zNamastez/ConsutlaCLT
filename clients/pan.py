import time, os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait, Select
from clients.digisac import Digisac

load_dotenv()

class Pan:
    def __init__(self):
        # Usa navegador já aberto na porta 9222
        self.options = Options()
        self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.driver = webdriver.Edge(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        self.digisac = Digisac()
    
    def _send_keys(self, by: str, value: str, keys: str) -> None:
        # Preenche campo com texto
        element = self.wait.until(expected_conditions.presence_of_element_located((by, value)))

        if element.is_enabled():
            element.click()
            element.send_keys(keys)
    
    def _click(self, by: str, value: str) -> None:
        # Clica em elemento
        try:
            element = self.wait.until(expected_conditions.element_to_be_clickable((by, value)))

            if element.is_enabled():
                self.driver.execute_script("arguments[0].click();", element)
        except:
            pass
    
    def _alert(self) -> None:
        # Aceita alertas, se tiver
        try:
            alert = self.wait.until(expected_conditions.alert_is_present())
            alert.accept()
        except:
            pass

    def get_link(self) -> None:
        # Abre o site
        self.driver.get("https://panconsig.pansolucoes.com.br/WebAutorizador/")
    
    def auth(self) -> None:
        # Faz login
        self._send_keys(By.CSS_SELECTOR, "#cpf-input > label > span.mahoe-input__input > input[type=text]", os.getenv("CPF"))
        self._click(By.ID, "form-partner-value")
        self._click(By.ID, "form-partner-0")
        self._click(By.CSS_SELECTOR, "button.mahoe-button__primary")
        
        try:
            self._send_keys(By.CSS_SELECTOR, "#senha > label > span.mahoe-input__input > input[type=password]", os.getenv("SENHA"))
            self._click(By.CSS_SELECTOR, "button.mahoe-button__primary")  
        except:
            pass       

    def FlMenu(self) -> None:
        # Lida com a tela de erro ou menu fechado
        while True:
            url = self.driver.current_url

            try:
                if "Erro.aspx" in url:
                    self._click(By.ID, "lnkVoltar")

                    break
                else:
                    div = self.driver.find_element(By.CSS_SELECTOR, "div.fechado.naoClicavel")

                    if div:
                        break
            except:
                pass

        self.driver.execute_script("arguments[0].style.display = 'block';", div)
        self._click(By.CSS_SELECTOR, "#block > a")

    def WebAutorizador(self) -> None:
        # Navega até a opção "Consulta Não Me Perturbe"
        menu_cadastro = self.wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//a[contains(., 'Cadastro') and contains(@class, 'dropdown-toggle')]")))
        ActionChains(self.driver).move_to_element(menu_cadastro).perform()

        consulta_nao_me_perturbe = self.wait.until(expected_conditions.visibility_of_element_located((By.XPATH, "//a[@href='/WebAutorizador/Cadastro/CardOferta' and contains(., 'Consulta Não Me Perturbe')]")))
        self.driver.execute_script("arguments[0].click();", consulta_nao_me_perturbe)

    def CardOferta(self, cpf: str, ddd: str, phone: str) -> None:
        # Preenche o formulário da oferta
        self.driver.refresh()

        select_empregador = self.wait.until(expected_conditions.presence_of_element_located((By.ID, "Empregador")))
        select = Select(select_empregador)
        time.sleep(1)
        select.select_by_value("000577")

        self._send_keys(By.ID, "CPF", cpf)

        ddd_input = self.driver.find_element(By.ID, "DDD")
        ddd_input.click()
        time.sleep(1)
        ddd_value = ddd_input.get_attribute("value")
        
        if not ddd_value:
            ddd_input.send_keys(ddd)

            self._send_keys(By.ID, "Telefone", phone)
        
        self._click(By.ID, "btnAceiteAutorizacaoCPD")

    def get_farol_title(self) -> str:
        # Verifica status da autorização
        time.sleep(1)

        while True:
            farol = self.driver.find_element(By.ID, "farolSolicitacaoId")
            title = farol.get_attribute("title")

            if not title:
                time.sleep(1)
                alert_div = self.wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "div.ui-dialog-content")))

                return alert_div.text

            if title not in ["Aguardando Resposta", "Aguardando Retorno"]:
                return title
            
            try:
                self._click(By.ID, "btnAceiteAutorizacaoCPD")
            except Exception as exception:
                print(f"[GET_FAROL_TITLE (EXCEPTION)]: {exception}")

    def start(self) -> None:
        # Executa a sequência inicial
        self.get_link()
        self.auth()
        self.get_link_login()
        self.FlMenu()
        self.WebAutorizador()

    def locate(self, data: dict) -> bool:
        # Decide o que fazer dependendo da URL
        url = self.driver.current_url
        
        if "CardOferta" in url:
            self.CardOferta(data["cpf"], data["ddd"], data["telefone"])
            
            return True
        elif "WebAutorizador" in url:
            self.WebAutorizador()
        elif "FIMenu" in url:
            self.FlMenu()
        elif "auth" in url:
            self.auth()
        
        return False
    
    def get_link_login(self) -> None:
        # Pega o link de login e envia via Digisac
        link_element = self.wait.until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, "a.qr-code__link[href]")))
        link = (link_element.get_attribute("href") or "").strip()

        if link.startswith("http"):
            self.digisac.send_message(f"Link pro login do PAN: {link}", os.getenv("NUMBER"))

    def consult(self) -> str | list:
        # Tenta consultar e simular ofertas
        time.sleep(3)
        self._click(By.ID, "btnConsultar")
        self._click(By.ID, "btnOfertarMargemLivre")

        try: 
            div = self.wait.until(expected_conditions.visibility_of_element_located((By.ID, "ui-id-1")))
                
            return div.text.strip()
        except:
            pass

        self._alert()
        
        periods = ["48", "42", "36", "30", "24", "18", "12", "6"]
        data = []

        for period in periods:
            # Muda o prazo da simulação
            period_dropdown = self.wait.until(expected_conditions.element_to_be_clickable((By.ID, "ctl00_Cph_ucP_JN_JpSim_cbPrz_CAMPO")))
            Select(period_dropdown).select_by_value(period)

            self._click(By.ID, "btnCalcular_txt")
            
            try:
                old_table = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_gvCond")
            except:
                old_table = None

            if old_table:
                try:
                    self.wait.until(expected_conditions.staleness_of(old_table))
                except TimeoutException:
                    pass
            
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_Cph_ucP_JN_JpSim_gvCond tr.normal, #ctl00_Cph_ucP_JN_JpSim_gvCond tr.alternate")
                num = len(rows)

                for i in range(num):
                    try:
                        rows = self.driver.find_elements(By.CSS_SELECTOR, "#ctl00_Cph_ucP_JN_JpSim_gvCond tr.normal, #ctl00_Cph_ucP_JN_JpSim_gvCond tr.alternate")
                        row = rows[i]
                        cells = row.find_elements(By.TAG_NAME, "td")

                        if len(cells) > 5:
                            raw = cells[5].text.strip()
                            value = float(raw.replace(".", "").replace(",", "."))

                            if value > 0.0:
                                checkbox = row.find_element(By.TAG_NAME, "input")
                                self.driver.execute_script("arguments[0].click();", checkbox)

                                self._alert()

                                self.wait.until(expected_conditions.visibility_of_element_located((By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc")))
                                span_parcela = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc_ctl03_lVlr")
                                span_prazo = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucCF_gvFinanc_ctl05_lVlr")
                                span_liberado = self.driver.find_element(By.ID, "ctl00_Cph_ucP_JN_JpSim_ucDSP_grdDespesas_ctl04_Label1")
                                
                                valor_parcela = span_parcela.text.strip()
                                prazo = span_prazo.text.strip()
                                valor_liberado = span_liberado.text.strip()
                                
                                data.append({
                                    "parcela": valor_parcela,
                                    "liberado": valor_liberado,
                                    "prazo": prazo
                                })

                    except Exception as exception:
                        print(f"[EXCEPTIION]: {exception}")
            except:
                pass
        
        self.get_link()

        return data           